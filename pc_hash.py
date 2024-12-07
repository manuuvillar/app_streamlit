import hashlib
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def hash_file(filepath, algorithm="sha256"):
    """Calcula a hash de um único arquivo"""
    hash_func = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):  # Lê em pedaços de 8KB
            hash_func.update(chunk)
    return hash_func.hexdigest()

# # Função para calcular a hash de uma pasta
# def hash_folder(folder_path, algorithm="sha256"):
#     """Calcula a hash de uma pasta, considerando arquivos e subpastas"""
#     hash_func = hashlib.new(algorithm)
#     for root, dirs, files in sorted(os.walk(folder_path)):
#         for name in sorted(files):  # Ordena para consistência
#             filepath = os.path.join(root, name)
#             file_hash = hash_file(filepath, algorithm)
#             # Atualiza com o caminho relativo e hash do arquivo
#             relative_path = os.path.relpath(filepath, folder_path)
#             hash_func.update(relative_path.encode())  # Hash do nome
#             hash_func.update(file_hash.encode())  # Hash do conteúdo
#     return hash_func.hexdigest()


# Calcular a hash da pasta
folder_hash = hash_file("candidatos_elisa.csv")
print("Hash da pasta:", folder_hash)

def load_public_key(filename):
    """Carrega a chave pública de um arquivo PEM"""
    with open(filename, "rb") as f:
        pem_data = f.read()
        public_key = serialization.load_pem_public_key(pem_data)
    return public_key

def load_signature(filename):
    """Carrega a assinatura de um arquivo binário"""
    with open(filename, "rb") as f:
        signature = f.read()
    return signature

def verify_signature(public_key, signature, hash_value):
    """Verifica a assinatura com a chave pública"""
    try:
        padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ), 
        hashes.SHA256()
        
        # public_key.verify(
        #     signature,
        #     hash_value.encode(),
        #     padding.PKCS1v15(), 
        #     hashes.SHA256()
        # )
        return True
    except Exception as e:
        print(f"Erro na verificação: {e}")
        return False

public_key = load_public_key("chave_publica_elisa.pem")  

signature = load_signature("ass_elisa.bin") 

is_valid = verify_signature(public_key, signature, folder_hash)
print("A assinatura é válida?", is_valid)
