import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from bs4 import BeautifulSoup
from langchain.text_splitter import TokenTextSplitter

from gpt import GPT

class Web_searcher:

    def __init__(self):
        self.url="https://www.googleapis.com/customsearch/v1"
        self.key="AIzaSyBVOPuxrh75cbTLecKr4ieho_ByMCh98qs"
        self.search_id="e3808504c0acd42f3"
        self.gpt=GPT()

    def web_load(self,phrase):
        payload={
            'key':self.key,
            'cx':self.search_id,
            'num':5,
            'q':phrase
        }
        res=requests.get(self.url, params=payload)
        content=[]
        if res.status_code==200:
            results=res.json()
            results=results['items']
            for result in results:
                content.append({'title':result['title'],'url':result['link'],'text':result['snippet']})
        return content

    def best_match(self, snippets, phrase):
        phrase_embedding = self.gpt.embedd_text(phrase)
        scores = []
        for snippet in snippets:
            snippet_embedding = self.gpt.embedd_text(snippet['text'])
            similarity = cosine_similarity([phrase_embedding], [snippet_embedding])[0][0]
            scores.append([similarity, snippet])
        new=sorted(scores, key=lambda x: x[0], reverse=True)
        return new

    def get_match(self, phrase):
        raw_results = self.web_load(phrase)
        scores = self.best_match(raw_results, phrase)

        # Retrieve and return the text of the best matched URL
        try:
            response = requests.get(scores[0][1]['url'],timeout=15,verify=False)
            response.raise_for_status()
            content_type = response.headers['Content-Type']
            text=""
            if 'pdf' in content_type:
                pdf_document = fitz.open(stream=response.content)
                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)
                    text += page.get_text()
            elif 'word' in content_type:
                docx_file = docx.Document(io.BytesIO(response.content))
                paragraphs = [paragraph.text for paragraph in docx_file.paragraphs]
                text='\n'.join(paragraphs)
            else:
                # For other content types like HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()

            #preprocess the text
            text=text.replace("\n"," ")
            text=text.replace("\xa0"," ")
            text=text.replace("\t"," ")
            text=text.replace("  "," ")
            text=text.replace("  "," ")
            text=text.replace("  "," ")
            snippet={'best match page':{'url':scores[0][1]['url'],'text':text},"full_results":raw_results}
            return snippet
        except Exception as e:
            print("Error on snippet after web search: "+str(e))
            return {"full_results":raw_results}

    def search(self, phrase):
        best_matched_text = self.get_match(phrase)
        return best_matched_text