import subprocess
import os

def executar_script(script_path):
    """Executa um script Python e retorna se foi bem-sucedido."""
    try:
        print(f"Iniciando a execução do script: {script_path}")
        # Executa o script com o Python e captura a saída e os erros
        result = subprocess.run(['python', script_path], capture_output=True, text=True)

        # Exibe a saída padrão e erros, se houver
        print(f"Saída do script {script_path}:\n{result.stdout}")
        if result.stderr:
            print(f"Erros do script {script_path}:\n{result.stderr}")

        # Verifica se a execução foi bem-sucedida
        if result.returncode == 0:
            print(f"Sucesso ao executar {script_path}")
            return True
        else:
            print(f"Erro ao executar {script_path}: {result.stderr}")
            return False
    except Exception as e:
        print(f"Erro ao tentar executar {script_path}: {str(e)}")
        return False

def main():
    print("Início da execução do controlador de scripts.")

    # Lista de scripts para executar em ordem
    scripts = [
        "automation_datapower_opsrecord.py",
        "Bot_lark_GA_files.py",
        "automation_GAperformance_1.0.py",
        "automation_CGVR.py",
        "automation_TCOR.py",
        #"automation_GAperformance_2.0.py"
    ]

    # Caminho onde os scripts estão localizados
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Executa cada script em ordem
    for script in scripts:
        script_path = os.path.join(script_dir, script)
        print(f"\nIniciando o script: {script}")
        sucesso = executar_script(script_path)
        
        # Se algum script falhar, interrompe a sequência
        if not sucesso:
            print("Interrompendo a execução devido a um erro.")
            break

    print("Execução do controlador de scripts concluída.")

if __name__ == "__main__":
    main()
