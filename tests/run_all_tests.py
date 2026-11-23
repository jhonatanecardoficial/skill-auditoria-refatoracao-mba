"""Executor unificado para as três suítes de teste do desafio refactor-arch."""

import os
import subprocess
import sys


def run_command(command, cwd=None):
    """Executa comando de teste capturando status e saída."""
    print(f"\n=======================================================")
    print(f"EXECUTANDO: {' '.join(command)}")
    print(f"DIRETÓRIO: {cwd or os.getcwd()}")
    print(f"=======================================================")
    result = subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    print(result.stdout)
    return result.returncode == 0


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    python_bin = sys.executable

    success = True

    # 1. Teste code-smells-project
    cmd_p1 = [python_bin, "-m", "unittest", "tests/test_code_smells_project.py"]
    if not run_command(cmd_p1, cwd=base_dir):
        print("❌ Falha nos testes de code-smells-project")
        success = False
    else:
        print("✅ Sucesso em code-smells-project")

    # 2. Teste ecommerce-api-legacy
    cmd_p2 = ["node", "tests/test_ecommerce_api.js"]
    if not run_command(cmd_p2, cwd=base_dir):
        print("❌ Falha nos testes de ecommerce-api-legacy")
        success = False
    else:
        print("✅ Sucesso em ecommerce-api-legacy")

    # 3. Teste task-manager-api
    cmd_p3 = [python_bin, "-m", "unittest", "tests/test_task_manager_api.py"]
    if not run_command(cmd_p3, cwd=base_dir):
        print("❌ Falha nos testes de task-manager-api")
        success = False
    else:
        print("✅ Sucesso em task-manager-api")

    print("\n" + "=" * 55)
    if success:
        print("🎉 TODOS OS TESTES DOS 3 PROJETOS FORAM APROVADOS!")
        print("=" * 55)
        sys.exit(0)
    else:
        print("🚨 HOUVE FALHA EM UMA OU MAIS SUÍTES DE TESTE!")
        print("=" * 55)
        sys.exit(1)


if __name__ == "__main__":
    main()
