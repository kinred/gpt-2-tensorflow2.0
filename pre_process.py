import tensorflow as tf
import numpy as np
from ftfy import fix_text
import sentencepiece as spm
from collections import Counter
import os
import datetime
import click
import tqdm
import glob
import csv

_ROOT = os.path.abspath(os.path.dirname(__file__))
PROCESS_DATA_PATH = _ROOT + "/data/processed.txt"
BPE_TSV_PATH = _ROOT + "/data/bpe_spm.tsv"
BPE_MODEL_PATH = _ROOT + "/data/bpe_model"
TF_RECORDS = _ROOT + "/data/tf_records/"
BOS_ID = 3
EOS_ID = 4


def process_text(text_files):
    print("Pre-processing the text data.....")
    file_writer = open(PROCESS_DATA_PATH, "w")
    for file_name in tqdm.tqdm(text_files):
        fr = open(file_name, 'r')
        file_writer.writelines([fix_text(line, normalization='NFKC') for line in fr.readlines()])
        fr.close
    file_writer.close()


def train_byte_pair_encoding(vocab_size):
    print("Training BytePair encoding......")
    token_dict = Counter()
    with open(PROCESS_DATA_PATH, 'r') as fr:
        for line in tqdm.tqdm(fr):
            token_dict.update(line.split())

    with open(BPE_TSV_PATH, 'w', newline='') as f_output:
        tsv_output = csv.writer(f_output, delimiter='\t')
        for word in token_dict:
            tsv_output.writerow([word, token_dict[word]])

    spmcmd = '--input={spm_input} --model_prefix={spm_model} --input_format=tsv --vocab_size={vocab_size} --user_defined_symbols=[SEP],[BOS],[EOS] --character_coverage=1.0 --hard_vocab_limit=true --model_type=bpe --pad_id=0 --unk_id=1 --bos_id=-1 --eos_id=-1 --pad_piece=[PAD] --unk_piece=[UNK]'.format(
        spm_input=BPE_TSV_PATH, spm_model=BPE_MODEL_PATH, vocab_size=vocab_size)

    spm.SentencePieceTrainer.train(spmcmd)


def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def serialize_example(inputs, targets):
    feature = {
        'inputs': _int64_feature(inputs),
        'targets': _int64_feature(targets)
    }
    example_proto = tf.train.Example(features=tf.train.Features(feature=feature))
    return example_proto.SerializeToString()


def create_tf_records(min_seq_len, max_seq_len, per_file_limit=50000):
    print("Creating TF Records...............")
    s = spm.SentencePieceProcessor()
    s.Load(BPE_MODEL_PATH + ".model")
    if not os.path.exists(TF_RECORDS):
        os.makedirs(TF_RECORDS)
    filename = TF_RECORDS + str(datetime.datetime.now().timestamp()) + ".tfrecord"
    tf_writer = tf.io.TFRecordWriter(filename)
    doc_counts = 0
    with open(PROCESS_DATA_PATH, 'r') as f:
        for line in tqdm.tqdm(f):
            encoded_id = s.encode_as_ids(line)
            if max_seq_len > len(encoded_id) > min_seq_len:
                inputs = np.array([BOS_ID] + encoded_id)
                targets = np.array(encoded_id + [EOS_ID])

                example = serialize_example(inputs, targets)
                tf_writer.write(example)
                doc_counts += 1
            if doc_counts >= per_file_limit:
                tf_writer.write(example)
                doc_counts = 0
                tf_writer.close()
                filename = TF_RECORDS + str(datetime.datetime.now().timestamp()) + ".tfrecord"
                tf_writer = tf.io.TFRecordWriter(filename)


@click.command()
@click.option('--data-dir', type=str, default="/data/scraped", show_default=True, help="training data path")
@click.option('--vocab-size', type=int, default=32000, show_default=True, help="byte pair vocab size")
@click.option('--min-seq-len', type=int, default=15, show_default=True, help="minimum sequence length")
@click.option('--max-seq-len', type=int, default=512, show_default=True, help="minimum sequence length")
def train(data_dir, vocab_size, min_seq_len, max_seq_len):
    text_files = glob.glob((_ROOT + data_dir + "/*.txt"))
    process_text(text_files)
    train_byte_pair_encoding(vocab_size)
    create_tf_records(min_seq_len, max_seq_len)


if __name__ == "__main__":
    train()
