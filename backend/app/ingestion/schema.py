"""Esquema de colunas dos arquivos brutos da unidade G1.

Ver docs/dicionario-de-dados.md para a origem de cada nome. O mapeamento é
por posição porque os 6 arquivos G1 compartilham exatamente o mesmo
cabeçalho (confirmado na auditoria do Marco 1).
"""

RAW_COLUMNS_G1 = [
    "timestamp",
    "generator_power",
    "unit_speed_pct",
    "temp_thrust_pad1",
    "temp_upper_guide_pad1",
    "temp_lower_guide_pad1",
    "temp_turbine_guide_pad1",
    "vib_ugb_x",
    "vib_ugb_y",
    "vib_ugb_z",
    "vib_lgb_x",
    "vib_lgb_y",
    "vib_tgb_x",
]

# Sinal central do projeto (mancal-guia da turbina).
PRIMARY_SIGNAL = "vib_tgb_x"

VALUE_COLUMNS = RAW_COLUMNS_G1[1:]

# Canal identificado como morto (100% zero) em 4 dos 6 meses — ver
# docs/relatorio-qualidade-dataset.md. Excluído por padrão da modelagem,
# mas preservado na ingestão para não descartar informação silenciosamente.
DEAD_CHANNEL = "temp_lower_guide_pad1"

MODELING_COLUMNS = [c for c in VALUE_COLUMNS if c != DEAD_CHANNEL]
