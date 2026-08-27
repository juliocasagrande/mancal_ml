# Dicionário de dados

Produzido por inspeção direta dos arquivos brutos em `data/raw/` (ver
`backend/scripts/audit_dataset.py`). A metadata pública do Figshare não
descreve as colunas — este dicionário é a única fonte de verdade sobre o
esquema.

## Arquivos e unidade geradora

O dataset contém dados de **duas unidades diferentes**, com esquemas de
coluna distintos e sem sobreposição temporal:

| Arquivo | Unidade | Período coberto | Linhas | Passo nominal |
|---|---|---:|---:|---|
| `June.csv` | G1 | 2020-06-01 a 2020-06-28 | 4000 | 10 min |
| `July.csv` | G1 | 2020-07-01 a 2020-07-28 | 4000 | 10 min |
| `Aug.csv` | G1 | 2020-08-01 a 2020-08-28 | 4000 | 10 min |
| `SEP.csv` | G1 | 2020-09-01 a 2020-09-28 | 4000 | 10 min |
| `Oct.csv` | G1 | 2020-10-01 a 2020-10-28 | 4000 | 10 min |
| `Nov.csv` | G1 | 2020-11-01 a 2020-11-28 | 4000 | 10 min |
| `vibration_data.csv` | G4 | 2021-10-01 a 2022-02-16 | 4000 | 50 min (irregular) |
| `vibration_data_G4_15-05-2022_to_10-05-2022.csv` | G4 | 2022-02-15 a 2022-05-09 | 4000 | 30 min |

**Decisão de escopo (ver `formulacao-do-problema.md`):** o MVP usa somente
os seis arquivos da unidade **G1**, que formam uma série contínua de seis
meses (junho a novembro de 2020) com o mesmo esquema de colunas. Os dois
arquivos da unidade G4 ficam fora do escopo do MVP.

## Esquema — arquivos G1 (`June.csv` … `Nov.csv`)

Cada arquivo tem 14 colunas (a 14ª é uma coluna vazia gerada por vírgula
final no cabeçalho — descartada na ingestão).

| Coluna (nome bruto) | Nome sugerido | Unidade física (assumida) | Descrição |
|---|---|---|---|
| `Point Name` | `timestamp` | — | Data/hora no formato `AAAA/MM/DD HH:MM:SS`, passo nominal de 10 min |
| `G1 Outlet Of Generator P` | `generator_power` | MW (assumido) | Potência de saída do gerador da Unidade G1 |
| `Neelum-Jhelum:AIN.G1 Unit Speed(GOV system)` | `unit_speed_pct` | % da velocidade nominal (assumido) | Velocidade da unidade reportada pelo sistema de governo (GOV) |
| `Neelum-Jhelum:AIN.G1 RIO1 thrust pad 1# temperature` | `temp_thrust_pad1` | °C (assumido) | Temperatura da sapata 1 do mancal de escora (thrust bearing) |
| `Neelum-Jhelum:AIN.G1 RIO1 upper guide pad 1# temperature` | `temp_upper_guide_pad1` | °C (assumido) | Temperatura da sapata 1 do mancal-guia superior (upper guide bearing, UGB) |
| `Neelum-Jhelum:AIN.G1 RIO1 lower guide pad 1# temperature` | `temp_lower_guide_pad1` | °C (assumido) | Temperatura da sapata 1 do mancal-guia inferior (lower guide bearing, LGB). **Canal com 100% de zeros em 4 dos 6 meses — ver relatório de qualidade.** |
| `Neelum-Jhelum:AIN.G1 RIO1 turbine guide pad 1# temperature` | `temp_turbine_guide_pad1` | °C (assumido) | Temperatura da sapata 1 do mancal-guia da turbina (turbine guide bearing, TGB) — **sinal central do projeto** |
| `Neelum-Jhelum:AIN.G1 vibrarion runout system UGB horizontal vibrarion +X` | `vib_ugb_x` | µm ou mm/s (não especificado na fonte) | Vibração horizontal do UGB, eixo +X |
| `Neelum-Jhelum:AIN.G1 vibrarion runout system UGB horizontal vibrarion -Y` | `vib_ugb_y` | idem | Vibração horizontal do UGB, eixo -Y |
| `Neelum-Jhelum:AIN.G1 vibrarion runout system UGB vertical vibrarion Z` | `vib_ugb_z` | idem | Vibração vertical do UGB, eixo Z |
| `Neelum-Jhelum:AIN.G1 vibrarion runout system LGB horizontal vibrarion +X` | `vib_lgb_x` | idem | Vibração horizontal do LGB, eixo +X |
| `Neelum-Jhelum:AIN.G1 vibrarion runout system LGB horizontal vibrarion -Y` | `vib_lgb_y` | idem | Vibração horizontal do LGB, eixo -Y |
| `Neelum-Jhelum:AIN.G1 vibrarion runout system TGB horizontal vibrarion +X` | `vib_tgb_x` | idem | Vibração horizontal do TGB, eixo +X — **sinal central do projeto** |

Observações:

- "RIO1" e "1#" no nome da tag sugerem que existe mais de uma sapata/ponto
  de medição por mancal na planta original, mas o dataset público expõe
  apenas o ponto 1. Não presumir cobertura completa do mancal.
  - O dataset **não inclui** vibração vertical (Z) nem horizontal -Y do
  TGB, apenas o eixo +X — assimetria de instrumentação a considerar na
  engenharia de atributos.
- A unidade física (µm, mm/s, g) dos canais de vibração não é informada
  pela fonte. Tratar como adimensional/relativo até validação com
  especialista; não converter para unidades de engenharia sem essa
  confirmação.
- Não existe, em nenhum arquivo, uma coluna categórica de rótulo
  (ex.: `status`, `fault`, `health_state`). Ver `formulacao-do-problema.md`.

## Esquema — arquivos G4 (fora do escopo do MVP)

`vibration_data.csv` tem 7 colunas de valor (potência + 6 canais de
vibração do UGB/LGB/TGB, sem colunas de temperatura).
`vibration_data_G4_15-05-2022_to_10-05-2022.csv` tem 10 colunas de valor,
incluindo dois canais adicionais (`UGB runout +X/-Y`) ausentes no outro
arquivo G4 e em todos os arquivos G1. Os dois arquivos G4 têm passo
temporal irregular (50 min e 30 min) e não descrevem o mesmo conjunto de
sensores entre si nem em relação a G1. Documentados aqui por completude;
não usados no pipeline do MVP.
