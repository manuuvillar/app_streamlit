import hashlib
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
"""Correr na VM"""
"""TEM QUE ENVIAR PARA O PC (POR EMAIL) A ASSINATURA E A CHAVE PUBLICA"""

# Função para calcular a hash de um arquivo
def hash_file(filepath, algorithm="sha256"):
    """Calcula a hash de um único arquivo"""
    hash_func = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):  
            hash_func.update(chunk)
    return hash_func.hexdigest()

def hash_folder(folder_path, algorithm="sha256"):
    """Calcula a hash de uma pasta, considerando arquivos e subpastas"""
    hash_func = hashlib.new(algorithm)
    for root, dirs, files in sorted(os.walk(folder_path)):
        for name in sorted(files):  # Ordena para consistência
            filepath = os.path.join(root, name)
            file_hash = hash_file(filepath, algorithm)
            # Atualiza com o caminho relativo e hash do arquivo
            relative_path = os.path.relpath(filepath, folder_path)
            hash_func.update(relative_path.encode())  # Hash do nome
            hash_func.update(file_hash.encode())  # Hash do conteúdo
    return hash_func.hexdigest()

def generate_keys():
    """Gera as chaves pública e privada"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

def sign_hash(private_key, hash_value):
    """Assina a hash com a chave privada"""
    signature = private_key.sign(
        hash_value.encode(),
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return signature

def save_public_key(public_key, filename):
    """Salva a chave pública em formato PEM"""
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(filename, "wb") as f:
        f.write(pem)

def save_signature(signature, filename):
    """Salva a assinatura digital em um arquivo binário"""
    with open(filename, "wb") as f:
        f.write(signature)



# 1. Calcular a hash da pasta
folder_hash = hash_folder("dados_universidades")
print("Hash da pasta:", folder_hash)

# 2. Gerar as chaves pública e privada
private_key, public_key = generate_keys()

# 3. Assinar a hash da pasta com a chave privada
signature = sign_hash(private_key, folder_hash)
print("Assinatura digital:", signature.hex())

save_public_key(public_key, "public_key.pem")
print("Chave pública salva em 'public_key.pem'")

# 5. Salvar a assinatura digital em um arquivo
save_signature(signature, "signature.bin")
print("Assinatura salva em 'signature.bin'")