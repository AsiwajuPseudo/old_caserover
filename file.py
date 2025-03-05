import io
import os
import fitz
import docx
import time
import random
from langchain.text_splitter import TokenTextSplitter

from gpt import GPT

class File:

  def __init__(self):
    self.gpt=GPT()


  #---------------------------------------------------------------------------------------
  def pdf_to_images(self,name, path,img_path):
    pdf_document = fitz.open(path+name)
    s=name.replace('.','-')
    new_path=img_path+s+"/"
    if not os.path.exists(new_path):
      os.makedirs(new_path)
    for page_number in range(len(pdf_document)):
      page = pdf_document.load_page(page_number)
      image = page.get_pixmap()
      image_path = f"{new_path}/page_{page_number + 1}.png"
      image.save(image_path)

  #---------------------------------------------------------------------------------------
  def load_path(self, path):
    # Check if the file exists
    if not os.path.exists(path):
        raise "error"

    # Determine the file type based on the file extension
    file_extension = os.path.splitext(path)[-1].lower()

    if file_extension == '.pdf':
        # For PDF files
        pdf_document = fitz.open(path)
        text = ''
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        return text
    elif file_extension == '.docx':
        # For .docx files
        docx_file = docx.Document(path)
        paragraphs = [paragraph.text for paragraph in docx_file.paragraphs]
        return '\n'.join(paragraphs)
    else:
        return "error"

  #---------------------------------------------------------------------------------------
  def download(self,path):
    try:
      text=self.load_path(path)
      text=text.replace('\n',' ')
      text=text.replace('\t',' ')
      text=text.replace('\xa0',' ')
      text=text.replace('  ',' ')
      text=text.replace('  ',' ')
      text=text.replace('  ',' ')

      return text
    except Exception as e:
      return "error"

  #----------------------------------------------------------------------------------------
  def mass_embedd(self,content):
    new = []
    i=0

    for item in content:
      # do a while, try 8 times
      attempts = 0
      while attempts < 8:
        try:
          vector = self.gpt.embedd_text(item['target'])
          id=item['path']+str(i)
          i=i+1
          new.append({"id":id, "values":vector, "metadata":item})
          break
        except Exception as e:
          attempts += 1
          print("Failed "+str(attempts)+" :"+str(e))
          time.sleep(1)  # Add a 1-second delay before the next retry
        ##
      #
    return new

  #-----------------------------------------------------------------------------------------
  def split_embed(self,text, size,pointers):
    #split document into set size
    overlap=int(size/3)
    large_chunk=size*3
    large_splitter = TokenTextSplitter(chunk_size=large_chunk, chunk_overlap=0)
    large_chunks=large_splitter.split_text(text)
    new_chunks=[]
    chunk_id=0
    name=pointers['name']
    for chunk in large_chunks:
      text_splitter = TokenTextSplitter(chunk_size=size, chunk_overlap=overlap)
      splitted_text=text_splitter.split_text(chunk)
      small=[]
      for small_chunk in splitted_text:
        meta = dict(pointers)
        small_chunk=name+ " is the name of this file. " + small_chunk
        meta['chunk_id']=chunk_id
        meta['text']=chunk
        meta['target']=small_chunk
        small.append(meta)
      new_chunks.extend(small)
      chunk_id=chunk_id+1
      #embed the new text
    vectors=self.mass_embedd(new_chunks)
    return vectors

  #------------------------------------------------------------------------------------------
  def process(self,pointers):
    path=pointers['path']
    text=self.download(path)
    if text=="error" or text=="type-error":
      return "error"
    else:
      #split and embedd text
      vectors=self.split_embed(text,300,pointers)
      return vectors