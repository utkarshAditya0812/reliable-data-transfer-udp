
# Reliable Data Transfer over UDP  (CS-30003 CA1 - P3)

Reliable file transfer over UDP using three ARQ protocols (Stop-and-Wait, Go-Back-N,
Selective Repeat), a home-made channel emulator, and SHA-256 integrity checks.

## Folder structure (one folder per member + one main folder)
| Folder | Owner | Contents |
|---|---|---|
| `arijeet_kundu/`   | Arijeet Kundu   | `checksum.py`, `packet.py` (packet format, sequence numbers), `stop_and_wait.py` |
| `utkarsh_aditya/`  | Utkarsh Aditya  | `go_back_n.py` (cumulative ACKs, sliding window) |
| `vedant_bhatnagar/`| Vedant Bhatnagar| `selective_repeat.py`, `rto.py` (Jacobson/Karels + Karn) |
| `shlok_jaiswal/`   | Shlok Jaiswal   | `channel_emulator.py`, `file_hash.py`, `run_experiments.py`, `plot_results.py`, `integrity_check.py` |
| `main_app/`        | (integration)   | **`main.py`** (the working file), `config.py`, `sample_input.txt` |
| `docs/`            | -               | 4 explanation PDFs (one per member) |
| `results/`         | -               | experiment CSVs and plots |

## How to run (Python 3.9+; only plotting needs `pip install matplotlib pandas`)
```bash
# one transfer, with 10% packet loss, using Selective Repeat
python main_app/main.py --protocol sr --input main_app/sample_input.txt --loss 0.1

# protocols: stop-and-wait | gbn | sr     other options: --window --duplicate --reorder --corrupt --seed --timeout

python shlok_jaiswal/integrity_check.py     # quick self-test of all 3 protocols
python shlok_jaiswal/run_experiments.py     # all experiments (a, b, c) -> results/*.csv
python shlok_jaiswal/plot_results.py        # results/*.png
```
