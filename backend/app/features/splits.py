"""Split temporal treino/validação/teste para a unidade G1.

Definido em docs/formulacao-do-problema.md a partir da auditoria do
Marco 1: cada arquivo mensal é uma fronteira rígida (não há dados dos
dias 29-31, então nenhuma janela pode atravessar a fronteira entre um
arquivo e o próximo). O split é feito por arquivo inteiro, nunca dentro
de um arquivo, o que garante trivialmente que nenhuma janela cruza uma
fronteira de split.

- treino: June.csv, July.csv (trecho saudável mais antigo)
- validação: Aug.csv (trecho saudável posterior)
- teste: SEP.csv, Oct.csv, Nov.csv (período futuro, contém os blocos de
  baixa atividade tratados como proxy fraco de anomalia)
"""

TRAIN_FILES = ["June.csv", "July.csv"]
VALIDATION_FILES = ["Aug.csv"]
TEST_FILES = ["SEP.csv", "Oct.csv", "Nov.csv"]

SPLIT_FILES = {
    "train": TRAIN_FILES,
    "validation": VALIDATION_FILES,
    "test": TEST_FILES,
}


def file_to_split(source_file: str) -> str:
    for split_name, files in SPLIT_FILES.items():
        if source_file in files:
            return split_name
    raise ValueError(f"Arquivo sem split definido: {source_file}")


def assign_split(df):
    """Adiciona a coluna 'split' com base em 'source_file'. Não faz cópia."""
    df["split"] = df["source_file"].map(file_to_split)
    if df["split"].isna().any():
        unknown = df.loc[df["split"].isna(), "source_file"].unique().tolist()
        raise ValueError(f"Arquivos sem split conhecido: {unknown}")
    return df
