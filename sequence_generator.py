from sample import SequenceGenerator
import click


@click.command()
@click.option('--model-path', type=str, default="./model", show_default=True, help="Model Path")
@click.option('--model-param', type=str, default="./model/model.json", show_default=True, help="Model Param")
@click.option('--vocab', type=str, default="./data/bpe_model.model", show_default=True, help="Vocab")
@click.option('--seq-len', type=int, default=512, show_default=True, help="seq_len")
@click.option('--temperature', type=float, default=1.0, show_default=True, help="seq_len")
@click.option('--top-k', type=int, default=8, show_default=True, help="seq_len")
@click.option('--top-p', type=float, default=0.9, show_default=True, help="seq_len")
@click.option('--nucleus_sampling', type=bool, default=True, show_default=True, help="seq_len")
@click.option('--context', type=str, default="", show_default=True, help="Context given to model")
def seq_gen(model_path, model_param, vocab, seq_len, temperature, top_k, top_p, nucleus_sampling, context):
    sg = SequenceGenerator(model_path, model_param, vocab)
    sg.load_weights()
    generated_seq = sg.sample_sequence(context,
                                     seq_len=512,
                                     temperature=1,
                                     top_k=8,
                                     top_p=0.9,
                                     nucleus_sampling=True)

    print(generated_seq)


if __name__ == "__main__":
    seq_gen()
