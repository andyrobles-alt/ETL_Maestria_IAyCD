"""Compila y ejecuta un notebook en un kernel Jupyter limpio del entorno actual."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import time

from jupyter_client import KernelManager


def execute_notebook(path, cwd):
    path, cwd = Path(path).resolve(), Path(cwd).resolve()
    original = path.read_bytes()
    notebook = json.loads(original.decode('utf-8'))
    cells = [cell for cell in notebook['cells'] if cell['cell_type'] == 'code']
    for index, cell in enumerate(cells, 1):
        compile(''.join(cell['source']), f'{path.name}:celda-{index}', 'exec')
        cell['outputs'] = []
        cell['execution_count'] = None
    print(f'{path.name}: {len(cells)} celdas compiladas.', flush=True)

    runtime = path.parent.parent / 'logs'
    runtime.mkdir(exist_ok=True)
    ipython_directory = runtime / 'ipython_eda'
    ipython_directory.mkdir(exist_ok=True)
    manager = KernelManager(
        kernel_name='python3', connection_file=str(runtime / f'kernel_eda_{os.getpid()}.json')
    )
    client = None
    try:
        launch = {
            'cwd': str(cwd),
            'extra_arguments': [
                '--HistoryManager.enabled=False',
                f'--IPKernelApp.ipython_dir={ipython_directory}',
                '--IPKernelApp.log_level=40',
            ],
        }
        if os.name == 'nt':
            launch['creationflags'] = subprocess.CREATE_NO_WINDOW
        manager.start_kernel(**launch)
        client = manager.blocking_client()
        client.start_channels()
        client.wait_for_ready(timeout=30)

        for index, cell in enumerate(cells, 1):
            message_id = client.execute(''.join(cell['source']), stop_on_error=True)
            deadline = time.monotonic() + 90
            error = None
            while True:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f'La celda {index} excedio 90 segundos.')
                try:
                    message = client.get_iopub_msg(timeout=1)
                except queue.Empty:
                    continue
                if message.get('parent_header', {}).get('msg_id') != message_id:
                    continue
                kind, content = message['msg_type'], message['content']
                if kind == 'execute_input':
                    cell['execution_count'] = content['execution_count']
                elif kind == 'stream':
                    cell['outputs'].append({
                        'output_type': 'stream', 'name': content['name'], 'text': content['text'],
                    })
                elif kind in {'display_data', 'execute_result'}:
                    output = {
                        'output_type': kind, 'data': content['data'], 'metadata': content['metadata'],
                    }
                    if kind == 'execute_result':
                        output['execution_count'] = content['execution_count']
                    cell['outputs'].append(output)
                elif kind == 'error':
                    error = content
                    cell['outputs'].append({
                        'output_type': 'error', 'ename': content['ename'],
                        'evalue': content['evalue'], 'traceback': content['traceback'],
                    })
                elif kind == 'clear_output':
                    cell['outputs'] = []
                elif kind == 'status' and content['execution_state'] == 'idle':
                    break
            while True:
                reply = client.get_shell_msg(timeout=30)
                if reply.get('parent_header', {}).get('msg_id') == message_id:
                    break
            if error or reply['content']['status'] != 'ok':
                details = error or reply['content']
                raise RuntimeError(f"Celda {index}: {details.get('ename')}: {details.get('evalue')}")
            print(f'Celda {index}: OK', flush=True)

        if hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(original).digest():
            raise RuntimeError('El archivo cambio durante la ejecucion; no se sobrescriben ediciones.')
        path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print(f'{path.name}: ejecucion completa sin errores; salidas guardadas.', flush=True)
    finally:
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
        if client is not None:
            client.stop_channels()
        manager.cleanup_resources()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('notebook', type=Path)
    parser.add_argument('--cwd', type=Path)
    args = parser.parse_args()
    execute_notebook(args.notebook, args.cwd or args.notebook.resolve().parent)
