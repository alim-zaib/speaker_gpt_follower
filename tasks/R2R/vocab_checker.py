import json
import argparse
import re
from collections import defaultdict


def load_vocab(vocab_file):
    with open(vocab_file, 'r') as file:
        vocab = set(file.read().splitlines())
    return vocab

def check_instructions(input_file, vocab):
    with open(input_file, 'r') as file:
        data = json.load(file)

    out_of_vocab = set()
    seen_words = set()
    word_pattern = re.compile(r'\b\w+\b')

    for item in data:
        for instruction in item['instructions']:
            words = word_pattern.findall(instruction)
            for word in words:
                if word in seen_words:
                    continue
                elif word not in vocab:
                    out_of_vocab.add(word)
                seen_words.add(word)

    return out_of_vocab

def main():
    parser = argparse.ArgumentParser(description="Check instructions against vocabulary.")
    parser.add_argument('input_file', type=str, help='Input JSON file path')
    parser.add_argument('vocab_file', type=str, help='Vocabulary file path')
    args = parser.parse_args()

    vocab = load_vocab(args.vocab_file)
    out_of_vocab_words = check_instructions(args.input_file, vocab)

    if out_of_vocab_words:
        print("Out of vocabulary words found:", out_of_vocab_words)
    else:
        print("No out of vocabulary words found.")

if __name__ == "__main__":
    main()
