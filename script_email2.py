import yagmail
import os

# Configuração do e-mail
sender_email = "minhavm109@gmail.com"
sender_password = "zbfx zmkl hgkg rliv"  # Substitua por sua senha ou app password
recipient_email = "minhavm109@gmail.com"
subject = "Chave pública e Assinatura Digital"
body = "Segue o arquivo em anexo."

# Caminhos absolutos para os arquivos de anexo
attachment_paths = [
    "signature.bin",  # Caminho relativo para o arquivo de assinatura
    "public_key.pem"  # Caminho relativo para a chave pública
]

# Verificando se os arquivos existem
for attachment in attachment_paths:
    if not os.path.isfile(attachment):
        print(f"Erro: O arquivo '{attachment}' não existe!")
        exit()

# Enviar o e-mail com yagmail
try:
    yag = yagmail.SMTP(sender_email, sender_password)
    
    # Tentando passar os arquivos como objetos de arquivo
    yag.send(
        to=recipient_email,
        subject=subject,
        contents=body,
        attachments=attachment_paths  # Passando os arquivos diretamente como paths
    )
    print("E-mail enviado com sucesso!")
except Exception as e:
    print(f"Erro ao enviar o e-mail: {e}")
