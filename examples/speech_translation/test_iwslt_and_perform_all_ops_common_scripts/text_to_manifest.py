import argparse
import json
from pathlib import Path
from typing import Dict, List, Union


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", "-i", required=True, type=Path, help="Path to input text transcript file.")
    parser.add_argument("--output", "-o", required=True, type=Path, help="Path to output NeMo manifest file.")
    parser.add_argument(
        "--reference_manifest",
        "-r",
        required=True,
        type=Path,
        help="Path to manifest file which will serve as a template for the output. `--reference_manifest` has to "
        "contain audio files used for creating `--input` transcript. The order of audio files in "
        "`--reference_manifest` has to be same as in `--input` file."
    )
    parser.add_argument(
        "--take_every_n_line",
        type=int,
        help="If scripts/asr_language_modeling/ngram_lm/eval_beamsearch_ngram.py is used to generate transcriptions, "
        "then all results from beam search are saved. For example, if `--beam_width` parameter of "
        "eval_beamsearch_ngram.py script is 4, then first 4 lines `--input` in transcript will be different expansions "
        "of 1 audio file. The first element in a beam has best score.",
        default=1,
    )
    args = parser.parse_args()
    for name in ['input', 'output', 'reference_manifest']:
        setattr(args, name, getattr(args, name).expanduser())
    return args


def load_manifest(manifest: Path) -> List[Dict[str, Union[str, float]]]:
    result = []
    with manifest.open() as f:
        for i, line in enumerate(f):
            data = json.loads(line)
            result.append(data)
    return result


def main() -> None:
    args = get_args()
    reference_manifest = load_manifest(args.reference_manifest)
    with args.output.open('w') as out_f, args.input.open() as in_f:
        for line, item in zip(in_f.readlines()[::args.take_every_n_line], reference_manifest):
            item = {"audio_filepath": item['audio_filepath'], "pred_text": line.split('\t')[0].strip()}
            out_f.write(json.dumps(item) + '\n')


if __name__ == "__main__":
    main()