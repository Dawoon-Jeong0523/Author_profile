# Run JSON schema (Preseen forecast task)

Documented from `preseen_exp/medicine/runs/control_rep01_<id removed>.json` (2026-10-01), as
saved by `nobel_preseen_exp.py poll` (`GET /forecasts/<task id>/?include_subforecasts=true`). The Physics and Chemistry
runs have the same structure.

## Task envelope

| key | type | meaning |
|---|---|---|
| `id` | str | task id (= `task_id` in `state.json`) |
| `type` | str | `forecast_task` |
| `status` | str | `completed` (also `failed`, `cancelled`; earlier `queued`, `running_subforecasts`, `synthesizing`) |
| `created_at`, `started_at`, `finished_at` | str (ISO, UTC) | timestamps; control rep01 took 26 min |
| `progress_message` | str | e.g. "Forecast generation completed." |
| `partial` | bool | false for a full forecast |
| `planned_subforecast_count`, `completed_subforecast_count` | int | 4 and 4 |
| `question` | object | the question as Preseen stores it: `title`, `description`, `resolution_criteria`, `fine_print`, `options`, `type`, bounds |
| `forecast` | object | the synthesized forecast (below) |
| `subforecasts` | list[4] | the component forecasts (below) |

## `forecast`

| key | type | meaning |
|---|---|---|
| `id`, `generated_at` | str | forecast id, time |
| `forecast_data.format` | str | `option_probabilities` |
| `forecast_data.question_type` | str | `multiple_choice` |
| `forecast_data.notes` | str | "Synthesized ensemble forecast." |
| `forecast_data.payload.probabilities` | dict {option text: float} | one probability per option, keys identical to the question's option texts (including "Other"); sums to 1 |
| `write_up` | str (markdown) | the forecast write-up (TL;DR, reasoning, links); 16,037 characters in control rep01 |
| `sources` | list[object] | `url`, `kind` (e.g. `tool`), `snippet`, `provider`, `cutoff_date`, `display_name`, `first_seen_at`; 297 in control rep01 |

## `subforecasts[i]`

| key | type | meaning |
|---|---|---|
| `sequence_index` | int | 0..3 |
| `status`, `completed_at` | str | `completed`, time |
| `forecast_data` | object | same format as the final forecast (`notes`: "Subforecast <n>") |
| `write_up`, `sources` | str, list | the subforecast's own write-up and sources |

## Used in `analyze.py`

- Final probabilities: `forecast.forecast_data.payload.probabilities`, matched to the question's options by exact text.
- Subforecast probabilities: `subforecasts[i].forecast_data.payload.probabilities`, by `sequence_index`.
- Write-up term counts: `forecast.write_up` (and the subforecast write-ups).
- Arm and rep: from the saved file name `<arm>_rep<NN>_<task id>.json`.
