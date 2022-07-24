import argparse
import logging
import os
import random
from pathlib import Path
from subprocess import PIPE, run
from typing import Union

from tqdm import tqdm

import prepare_small_data_for_punctuation_capitalization_task as small


logging.basicConfig(level="INFO", format='%(levelname)s -%(asctime)s - %(name)s - %(message)s')


BUFF_SIZE = 2 ** 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input_file", type=Path, required=True)
    parser.add_argument("--output_file", type=Path, required=True)
    parser.add_argument("--start_length", type=int, default=3)
    parser.add_argument("--end_length", type=int, default=128)
    parser.add_argument("--num_passes_through_dataset", type=int, default=1)
    args = parser.parse_args()
    args.input_file = args.input_file.expanduser()
    args.output_file = args.output_file.expanduser()
    return args


def get_num_characters(input_file: Union[str, os.PathLike]) -> int:
    result = run(['wc', '-m', str(input_file)], stdout=PIPE, stderr=PIPE)
    if not result:
        raise ValueError(
            f"Bash command `wc -m {input_file}` returned and empty string. "
            f"Possibly, file {input_file} does not exist."
        )
    return int(result.stdout.decode('utf-8').split()[0])


def main() -> None:
    args = parse_args()
    perm = list(range(args.start_length, args.end_length))
    random.shuffle(perm)
    p_i = 0  # index of segment length in permutation `perm`
    b_i = 0  # An index of first not processed character in buffer
    logging.info(f"Calculating number of characters in file {args.input_file} using command `wc -m {args.input_file}`")
    num_characters = get_num_characters(args.input_file)
    progress_bar = tqdm(total=num_characters * args.num_passes_through_dataset, desc="Cutting segments", unit="char")
    with args.output_file.open('w', buffering=BUFF_SIZE) as out_f:
        for _ in range(args.num_passes_through_dataset):
            with args.input_file.open(buffering=BUFF_SIZE) as in_f:
                buff = ""
                last_match = None
                while True:
                    read_chunks_len = 0
                    buff = buff[b_i:]
                    b_i = 0
                    chunk = in_f.read(BUFF_SIZE)
                    if not chunk:
                        if last_match is not None:
                            out_f.write(buff[b_i : b_i + last_match.span()[1]] + '\n')
                            b_i += last_match.span()[1]
                        break
                    buff += chunk.replace('\n', ' ')
                    read_chunks_len += len(chunk)
                    last_match = None
                    start_m_i = 0
                    for m_i, m in enumerate(small.WORD_WITH_PRECEDING_AND_FOLLOWING_PUNCTUATION.finditer(buff[b_i:])):
                        last_match = m
                        if m_i - start_m_i >= perm[p_i] - 1:
                            out_f.write(buff[b_i : m.span()[1]] + '\n')
                            b_i = m.span()[1]
                            start_m_i = m_i
                            p_i = (p_i + 1) % len(perm)
                            if p_i == 0:
                                random.shuffle(perm)
                    progress_bar.update(read_chunks_len)
    progress_bar.close()


if __name__ == "__main__":
    main()