"""JSON boundary for offline clients using the same calculation engine as GTK."""
from dataclasses import asdict
from datetime import datetime, timezone
import json
import math
from .registry import TOOLS, GROUPS, TOOL_SCOPE
from .calculators import CALCS
from .guidance import guide
from ..identity import VERSION

MAX_REQUEST = 100_000

def catalog():
    groups = dict(GROUPS)
    return [{'id': t[0], 'group': groups[t[1]], 'title': t[2], 'description': t[3],
             'fields': t[4], 'guide': guide(t[0])} for t in TOOLS]

def _finite_tree(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError('O resultado excede o domínio numérico. Revise a escala das entradas.')
    if isinstance(value, dict):
        for child in value.values(): _finite_tree(child)
    elif isinstance(value, (list, tuple)):
        for child in value: _finite_tree(child)

def calculate(tool_id, inputs):
    tool = next((t for t in TOOLS if t[0] == tool_id), None)
    if tool is None or not isinstance(inputs, dict):
        raise ValueError('Ferramenta ou entradas inválidas.')
    fields = {f['key']: f for f in tool[4]}
    if set(inputs) != set(fields):
        raise ValueError('As entradas devem corresponder aos campos da ferramenta.')
    for key, value in inputs.items():
        if not isinstance(value, str) or len(value) > 20000:
            raise ValueError('Entrada inválida ou muito longa: ' + key)
        if fields[key]['kind'] == 'select' and value not in fields[key]['options']:
            raise ValueError('Opção inválida: ' + key)
    result = asdict(CALCS[tool_id](inputs))
    _finite_tree(result)
    return {'schema': 1, 'version': VERSION, 'calculator': tool_id, 'title': tool[2],
            'created_utc': datetime.now(timezone.utc).isoformat(), 'inputs': dict(inputs),
            'input_labels': {k: f['label'] for k, f in fields.items()},
            'scope': TOOL_SCOPE[tool_id][1], 'result': result}

def dispatch(request):
    try:
        if not isinstance(request, str) or len(request) > MAX_REQUEST:
            raise ValueError('Pedido inválido ou muito grande.')
        data = json.loads(request)
        if not isinstance(data, dict): raise ValueError('Pedido deve ser um objeto.')
        if data.get('operation') == 'catalog':
            payload = catalog()
        elif data.get('operation') == 'calculate':
            payload = calculate(data.get('tool'), data.get('inputs'))
        else:
            raise ValueError('Operação desconhecida.')
        return json.dumps({'ok': True, 'payload': payload}, ensure_ascii=False, allow_nan=False)
    except (ValueError, TypeError, KeyError, ArithmeticError) as exc:
        return json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False)
