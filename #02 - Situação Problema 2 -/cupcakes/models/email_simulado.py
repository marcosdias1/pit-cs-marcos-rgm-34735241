# envio de e-mail SIMULADO
# o projeto não tem servidor de e-mail, então em vez de mandar de verdade o e-mail aparece no terminal onde o Flask está rodando (assim dá pra mostrar no vídeo que o sistema "enviou")
# numa loja de verdade, esta função seria trocada por um envio de e-mail de verdade


# função que "envia" o e-mail: escreve ele no terminal
def enviar(destino, assunto, texto):
    print("")
    print("=" * 60)
    print("E-MAIL SIMULADO (não foi enviado de verdade)")
    print("Para: " + destino)
    print("Assunto: " + assunto)
    print("-" * 60)
    print(texto)
    print("=" * 60)
    print("")