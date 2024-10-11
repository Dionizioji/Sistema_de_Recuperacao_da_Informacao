from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
import re
from collections import defaultdict
import requests
from unidecode import unidecode

class Coletor:
    def __init__(self):
        self.urls_visitadas = set()  # Conjunto para armazenar URLs já visitadas
        self.dados_coletados = []    # Lista para armazenar os dados coletados

    def coletar_urls(self, url_inicial, profundidade=1):
        """Método para coletar URLs recursivamente até uma determinada profundidade"""
        if profundidade == 0:
            return
        if url_inicial in self.urls_visitadas:
            return

        url_objeto = Url(url_inicial)
        html = url_objeto.buscar_html()
        if html:
            self.urls_visitadas.add(url_inicial)

            soup = BeautifulSoup(html, 'html.parser')  # Cria um objeto BeautifulSoup para análise HTML
            tags_a = soup.find_all('a', href=True)  # Encontra todas as tags 'a' com atributo 'href'

            autores = [a.get_text() for a in soup.find_all('a', class_='author')]  # Encontra os autores na página

            for tag_a in tags_a:
                href = tag_a['href']  # Obtém o atributo 'href' da tag 'a'
                href_absoluto = urljoin(url_inicial, href)  # Une a URL base com a URL relativa
                if self.validar_url(href_absoluto):  # Verifica se a URL é válida
                    self.dados_coletados.append({'url': href_absoluto, 'autores': autores})  # Adiciona a URL e os autores aos dados coletados
                    self.coletar_urls(href_absoluto, profundidade - 1)  # Chama recursivamente para coletar mais URLs

    def validar_url(self, url):
        """Método para validar se a URL está no formato desejado"""
        return re.match(r'^https://www\.monografias\.ufop\.br/handle/\d{8}/\d{4}$', url)  # Verifica o formato da URL

    def salvar_dados_json(self, nome_arquivo):
        """Método para salvar os dados coletados em um arquivo JSON"""
        with open(nome_arquivo, 'w') as arquivo:
            json.dump(self.dados_coletados, arquivo, indent=4)  # Salva os dados coletados em formato JSON

    def indexar_autores(self, indexador):
        """Método para indexar autores em todas as URLs coletadas"""
        for dado in self.dados_coletados:
            url = dado['url']
            autores = dado['autores']  # Obtém os autores da URL
            indexador.indexar_pagina(url, autores)  # Indexa os autores na URL

class Url:
    def __init__(self, url):
        self.url = url

    def buscar_html(self):
        """Método para buscar o HTML de uma URL"""
        try:
            resposta = requests.get(self.url, allow_redirects=True)  # Realiza uma solicitação HTTP para obter o HTML
            if resposta.history:
                print(f"Redirecionamento detectado para a URL: {self.url}")  # Imprime se houve redirecionamento
                self.url = resposta.url  # Atualiza a URL se houve redirecionamento
            if resposta.status_code == 200:
                return resposta.text  # Retorna o texto do HTML se a solicitação foi bem-sucedida
            else:
                print(f"Falha ao buscar o HTML de {self.url}. Código do erro: {resposta.status_code}")  # Imprime mensagem de erro
                return None
        except requests.exceptions.RequestException as erro:
            print(f"Ocorreu um erro ao buscar o HTML de {self.url}: {str(erro)}")  # Imprime mensagem de erro
            return None

class Indexador:
    def __init__(self):
        self.indice_invertido = defaultdict(list)  # Cria um dicionário com listas como valores padrão
        self.autores_tokens = defaultdict(lambda: defaultdict(int))  # Dicionário para armazenar a contagem de tokens por autor

    def indexar_pagina(self, url, autores):
        """Método para indexar os autores encontrados em uma página"""
        for autor in autores:
            autor_normalizado = unidecode(autor)  # Normaliza o nome do autor
            self.indice_invertido[autor_normalizado].append(url)  # Adiciona a URL ao índice invertido do autor
            tokens = autor_normalizado.lower().split()  # Tokeniza o nome do autor
            for token in tokens:
                self.autores_tokens[autor_normalizado][token] += 1  # Incrementa a contagem do token para o autor

    def buscar(self, termo):
        """Método para buscar URLs por termo de pesquisa (link ou nome do autor)"""
        resultados = []
        termo_normalizado = unidecode(termo.lower())  # Normaliza o termo de pesquisa
        termo_tokens = termo_normalizado.split()  # Tokeniza a consulta
        resultados_pontuados = defaultdict(int)  # Dicionário para armazenar a pontuação dos resultados

        for autor, urls in self.indice_invertido.items():
            autor_tokens = autor.lower().split()  # Tokeniza o nome do autor na base de dados
            for token in termo_tokens:
                for autor_token in autor_tokens:
                    if token in autor_token:
                        resultados_pontuados[autor] += self.autores_tokens[autor][autor_token]  # Incrementa a pontuação

        # Ordena os resultados por pontuação
        resultados_ordenados = sorted(resultados_pontuados.items(), key=lambda x: x[1], reverse=True)

        for autor, pontuacao in resultados_ordenados:
            resultados.extend(self.indice_invertido[autor])

        return resultados

if __name__ == "__main__":
    urls = [
        "https://www.monografias.ufop.br/handle/35400000/73/simple-search?filterquery=2023&filtername=dateIssued&filtertype=equals",
        "https://www.monografias.ufop.br/handle/35400000/73/simple-search?filterquery=2023&filtername=dateIssued&filtertype=equals",
        "https://www.monografias.ufop.br/handle/35400000/73/simple-search?filterquery=2022&filtername=dateIssued&filtertype=equals",
        "https://www.monografias.ufop.br/handle/35400000/73/simple-search?filterquery=2021&filtername=dateIssued&filtertype=equals",
        "https://www.monografias.ufop.br/handle/35400000/73/simple-search?filterquery=2020&filtername=dateIssued&filtertype=equals",

        "https://www.monografias.ufop.br/handle/35400000/73/simple-search?filterquery=2019&filtername=dateIssued&filtertype=equals",
        "https://www.monografias.ufop.br/handle/35400000/73/simple-search?filterquery=2018&filtername=dateIssued&filtertype=equals",
        "https://www.monografias.ufop.br/handle/35400000/73/simple-search?filterquery=2017&filtername=dateIssued&filtertype=equals",
        "https://www.monografias.ufop.br/handle/35400000/73/simple-search?filterquery=2016&filtername=dateIssued&filtertype=equals",
        "https://www.monografias.ufop.br/handle/35400000/73/simple-search?filterquery=2015&filtername=dateIssued&filtertype=equals",
        "https://www.monografias.ufop.br/handle/35400000/73/simple-search?filterquery=2014&filtername=dateIssued&filtertype=equals"
    ]

    coletor = Coletor()  # Instancia um objeto da classe Coletor
    indexador = Indexador()  # Instancia um objeto da classe Indexador

    for url in urls:
        coletor.coletar_urls(url, profundidade=3)  # Coleta as URLs com profundidade aumentada para 3

    coletor.salvar_dados_json('dados_coletados.json')  # Salva os dados coletados em um arquivo JSON
    coletor.indexar_autores(indexador)  # Indexa os autores em todas as URLs coletadas

    while True:
        consulta = input("Digite o termo de pesquisa (nome do autor ou parte do link) ou 'sair' para encerrar: ")
        if consulta.lower() == 'sair':
            break
        resultados = indexador.buscar(consulta)
        if resultados:
            print("URLs encontradas:")
            for url in resultados:
                print(url)
        else:
            print("Nenhuma URL encontrada.")