"""Transporte de timestamp não-ambíguo (M18).

Fonte única do "marcar UTC": converte um datetime naive-UTC (como gravado via
`datetime.utcnow`, sem tzinfo) em ISO-8601 com sufixo `Z`, para que o cliente
possa convertê-lo ao fuso do dispositivo sem ambiguidade.

Divisão de responsabilidade (1 fonte por modo de render):
- **Marcação UTC (servidor):** esta função `utc_iso` — usada por to_dict()/rotas e
  pelo filtro Jinja `utc_iso` (registrado em app.py), consumido pela macro
  `local_dt` em _macros.html.
- **Formatação humana (cliente):** `formatLocalDT(iso, fmt)` em base.html — único
  ponto que escolhe `dd/mm/aaaa [HH:MM]` e aplica o fuso do browser.

O armazenamento permanece naive UTC — nada aqui escreve no banco.
"""
from datetime import timezone


def utc_iso(dt):
    """datetime naive-UTC → ISO-8601 com 'Z' (não-ambíguo). '' para None.

    Naive é assumido como UTC (contrato do app: tudo gravado via utcnow).
    Aware é normalizado para UTC. A formatação humana é feita só no cliente.
    """
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")
