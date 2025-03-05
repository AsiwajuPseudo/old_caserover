#pip install flask requests PyMuPDF python-docx openpyxl langchain tiktoken chromadb openai==0.28.1 flask-cors pandas beautifulsoup4 fuzzywuzzy python-Levenshtein networkx scikit-learn --break-system-packages
from flask import Flask, request, render_template,send_file, jsonify, make_response
from datetime import datetime
from fuzzywuzzy import fuzz, process
import requests
import json
import random
import csv
import io
import os
from flask_cors import CORS

#local libraries
from database import Database
from file_control import File_Control
from collector import Collector
from process import Process
from euclid import Euclid
from graph import Graph
from tools import Tools
from file import File
from temp_file import create_dir,delete_dir, generate_tree, get_dir,process_path,move_files, deli_file, search_file

database=Database()
collections=Euclid()

app = Flask(__name__)
CORS(app)




#--------------------------------------------------------------------------------------------------------------
#AUTH AND ACCOUNT

#lping the system
@app.route('/ping', methods=['GET'])
def ping():
  return {'status':'running'}

#login to account
@app.route('/login', methods=['POST'])
def render1():
  data = request.get_json()
  email=data.get('email')
  password=data.get('password')
  log=database.login(email,password)
  return log

#login to account
@app.route('/editorlogin', methods=['POST'])
def editor_login():
  data = request.get_json()
  email=data.get('email')
  password=data.get('password')
  log=database.login(email,password)
  return log

#admin login to account
@app.route('/adminlogin', methods=['POST'])
def adminlogin():
  data = request.get_json()
  email=data.get('email')
  password=data.get('password')
  key=data.get('key')
  if key=="0000admincenter0000":
    log=database.adminlogin(email,password)
    return log
  else:
    return {'status':'Account not authorized to be admin'}

@app.route('/register', methods=['POST'])
def render2():
  data = request.get_json()
  name=data.get('name')
  email=data.get('email')
  atype=data.get('type')
  code=data.get('code')
  password=data.get('password')
  phone=data.get('phone')
  add=database.add_user(name,email,phone,atype,code,password)
  return add

#--------------------------------------------------CASE ROVER MAIN METHODS

#view user profile
@app.route('/profile', methods=['GET'])
def view_profile():
  user_id=request.args.get('user_id')
  profile=database.user_profile(user_id)
  return profile

#view user profile
@app.route('/allusers', methods=['GET'])
def view_profiles():
  user_id=request.args.get('user_id')
  profile=database.user_profile(user_id)
  users=database.profiles()
  return {'users':users,'profile':profile}

@app.route('/subscribe_user', methods=['POST'])
def subscribe_user():
  data = request.get_json()
  user_id=data.get('user_id')
  next_date=data.get('next_date')
  update=database.subscribe_user(user_id,next_date)
  users=database.profiles()
  return {'status':update,'users':users}

@app.route('/subscribe_org', methods=['POST'])
def subscribe_orginisation():
  data = request.get_json()
  code=data.get('code')
  next_date=data.get('next_date')
  update=database.subscribe_org(code,next_date)
  users=database.profiles()
  return {'status':update,'users':users}

#delete a user profile
@app.route('/delete_user', methods=['GET'])
def delete_profile():
  user_id=request.args.get('user_id')
  op=database.deli_user(user_id)
  users=database.profiles()
  return {'users':users}

#change password
@app.route('/password', methods=['POST'])
def change_password():
  data = request.get_json()
  oldpassword=data.get('oldpassword')
  newpassword=data.get('newpassword')
  user_id=data.get('user_id')
  passwd=database.passchange(user_id,oldpassword,newpassword)
  return passwd

#run
@app.route('/run', methods=['POST'])
def run_model():
  data = request.get_json()
  tool=data.get('tool')
  tools=Tools(collections)
  if tool=="assistant":
    prompt=data.get('prompt')
    size=data.get('size')
    answer=tools.assistant(prompt,size)
  elif tool=="rag":
    table=data.get('table')
    prompt=data.get('prompt')
    k=data.get('k')
    size=data.get('size')
    answer=tools.rag(table,prompt,k,size)
  elif tool=="web":
    phrase=data.get('phrase')
    size=data.get('size')
    answer=tools.web_search(phrase,size)
  elif tool=="frag":
    table=data.get('table')
    prompt=data.get('prompt')
    k=data.get('k')
    size=data.get('size')
    answer=tools.frag(table,prompt,k,size)
  else:
    answer={"answer":"Unknown model"}

  return answer

#add a chat
@app.route('/add_chat', methods=['POST'])
def add_chat():
  data = request.get_json()
  name=data.get('name')
  user=data.get('user_id')
  add=database.add_chat(user,name)
  chats=database.chats(user)
  return {"status":add,"chats":chats}

#delete a chat
@app.route('/deli_chat', methods=['GET'])
def deli_chat():
  chat=request.args.get('chat_id')
  user=request.args.get('user_id')
  deli=database.deli_chat(chat)
  chats=database.chats(user)

  return {"status":deli,"chats":chats}

#retrieve all chats belonging to a user
@app.route('/allchats', methods=['GET'])
def collect_all_chats():
  chats=database.allchats()
  tables=collections.tables()
  table_data=[]
  tables_list=[]
  for col in tables:
    tables_list.append(col.name)

  return {"chats":chats,"tables":tables_list}

#retrieve all chats belonging to a user
@app.route('/messagesanduser', methods=['GET'])
def collect_messages_and_user():
  chat=request.args.get('chat_id')
  user=request.args.get('user_id')
  messages=database.messages(chat)
  path="./files/uploads/"+chat+"/"
  nodes=generate_tree(path)
  profile=database.user_profile(user)

  return {"messages":messages,"nodes":nodes,"user":profile}

#retrieve all chats belonging to a user
@app.route('/chats', methods=['GET'])
def collect_chats():
  user=request.args.get('user_id')
  chats=database.chats(user)
  tables=collections.tables()
  table_data=[]
  tables_list=[]
  for col in tables:
    tables_list.append(col.name)

  return {"chats":chats,"tables":tables_list}

#retrieve all chats belonging to a user
@app.route('/messages', methods=['GET'])
def collect_messages():
  chat=request.args.get('chat_id')
  messages=database.messages(chat)
  path="./files/uploads/"+chat+"/"
  nodes=generate_tree(path)

  return {"messages":messages,"nodes":nodes}

#playground
@app.route('/play', methods=['POST'])
def run_playground():
  data = request.get_json()
  chat = data.get('chat_id')
  user = data.get('user_id')
  prompt = data.get('prompt')
  tool = data.get('tool')
  tools = Tools(collections)
  # Check if there is a valid chat or it's a new one
  if chat == '' or chat is None:
    i = str(random.randint(1000, 9999))
    name = "space_" + i
    add = database.add_chat(user, name)
    chat = add['chat']
  # Execute
  try:
    if tool == "assistant":
      history = database.messages(chat)
      answer, sources = tools.assistant(prompt, 4060, history)
    elif tool == "web":
      history = database.messages(chat)
      answer, sources = tools.web_search(prompt, 4060, history)
    elif tool == "documents":
      # List all files from the directory
      history = database.messages(chat)
      files = os.listdir('./files/uploads/' + chat + '/')
      text = ""
      for file in files:
        t = File()
        data = {"document_name": file, "content": t.download('./files/uploads/' + chat + '/' + file)}
        text = text + str(data)
      # Check if there was a document
      if text == "":
        return "Please upload a document to be able to use this tool", []
      # Generate answer if document is available
      answer = tools.extracter(prompt, 4060, text, history)
      sources = files
    else:
      history = database.messages(chat)
      answer, sources = tools.rag(tool, prompt, history, 3, 4060)
  except Exception as e:
    print(e)
    p={"answer":[{"type":"paragraph","data":"Error generating content, please try again. If the error persist create a new workspace."}],"sources":[]}
    answer=json.dumps(p)
    sources=[]

  # Add answer to database
  add = database.add_message(chat, user, str(answer), prompt)
  messages = database.messages(chat)
  chats = database.chats(user)

  return {"messages": messages, "documents": sources, "chats": chats, "current": chat}


#upload files for GPT
@app.route('/cloudupload', methods=['POST'])
def upload_files_gpt():
  chat = request.form.get('chat_id')
  transcript=[]
  files = request.files.getlist('files')
  if len(files) == 0:
    return {"status":"No file part"}
  # Create a temporary directory
  path="./files/uploads/"+chat+"/"
  folder=create_dir(path)
  if folder['message']=='error':
    return {"status":"Error creating folder"}
  # Save each file to the temporary directory
  for file in files:
    if file.filename == '':
      continue
    filename = os.path.join(path, file.filename)
    file.save(filename)
    name=file.filename
    '''
    if name.endswith('.pdf'):
      new_path="./files/pdf_images/"+chat+"/"
      folder=create_dir(new_path)
      t=File()
      t.pdf_to_images(name,path,new_path)
      vis=Vision()
      pages=vis.pdf_vision(name, new_path)
      print(pages)'''
  #upload files
  nodes=generate_tree(path)
  return {"status":"success",'nodes':nodes}

@app.route('/source', methods=['GET'])
def get_source():
  tool=request.args.get('tool')
  name=request.args.get('name')
  if tool=="assistant":
    return "Load html content"
  elif tool=="web":
    return {"url":name}
  elif tool=="documents":
    chat=request.args.get('chat_id')
    file="./files/uploads/"+chat+"/"+name
    return send_file(file, as_attachment=False)
  else:
    #search for the document
    file=search_file('./files/closed/'+tool+'/',name)
    if file:
      return send_file(file, as_attachment=False)
    else:
      return "File not found"


#show cloud tree
@app.route('/cloud_tree', methods=['GET'])
def cloud_tree():
  chat=request.args.get('chat_id')
  path="./files/uploads/"+chat+"/"
  nodes=generate_tree(path)

  return {"nodes":nodes}

#delete file from cloud
@app.route('/delete_cloud', methods=['GET'])
def delete_cloud_tree():
  chat=request.args.get('chat_id')
  file=request.args.get('name')
  path="./files/uploads/"+chat+"/"
  file_path=path+file
  os.remove(file_path)
  if file.endswith('.pdf'):
    dir_name=file.replace('.','-')
    new_path="./files/pdf_images/"+chat+"/"
    n=delete_dir(new_path+dir_name+'/')
  nodes=generate_tree(path)

  return {"nodes":nodes}

@app.route('/get_pdf')
def get_pdf():
    return send_file('path/to/your/pdf/file.pdf', as_attachment=False)

#view directories
@app.route('/dir', methods=['GET'])
def dir():
  content=get_dir('./files/')

  return content

#view directories
@app.route('/t_del', methods=['GET'])
def delete_database_table():
  table=request.args.get('table')
  deli=database.delete_table(table)

  return deli


#--------------------------------------------------EDITOR MODE METHODS

#Load all the tables currently created
@app.route('/tables', methods=['GET'])
def tables():
  #check if tables object exist
  if File_Control.check_path('./tables/') and File_Control.check_path('./tables/root.pkl'):
    tables=File_Control.open('./tables/root.pkl')
  else:
    #create folder
    File_Control.create_path('./tables/')
    tables=[]
    File_Control.save('./tables/root.pkl',tables)
    File_Control.save('./tables/files.pkl',tables)
  return {"tables":tables}

#create a table
@app.route('/add_table', methods=['POST'])
def create_table():
  data = request.get_json()
  name=data.get('name')
  type=data.get('type')
  #view what is in the tables
  tables=File_Control.open('./tables/root.pkl')
  vector=Euclid()
  add=vector.create_table(name)
  if add=='success':
    table_id=str(random.randint(1000,9999))
    table={"id":table_id,"name":name,"type":type,'count':0}
    tables.append(table)
    File_Control.save('./tables/root.pkl',tables)
    files=[]
    File_Control.save('./tables/'+name+'-'+table_id+'.pkl',files)
    File_Control.create_path('./temp/'+name+'-'+table_id+'/')
    File_Control.create_path('./data/'+name+'-'+table_id+'/')

    return {"result":"success","tables":tables}
  else:
    return {"result":"error creating vector database table, check table name","tables":tables}

#delete a table
@app.route('/delete_table', methods=['GET'])
def delete_table():
  table=request.args.get('id')
  name=request.args.get('name')
  tables=File_Control.open('./tables/root.pkl')
  vector=Euclid()
  dele=vector.delete_table(name)
  if dele=='success':
    files=File_Control.open('./tables/files.pkl')
    new_files=[item for item in files if item['table_id'] != table]
    new_tables=[item for item in tables if item['id'] != table]
    File_Control.save('./tables/root.pkl',new_tables)
    File_Control.save('./tables/files.pkl',new_files)
    File_Control.delete_file('./tables/'+name+'-'+table+'.pkl')
    tables=File_Control.open('./tables/root.pkl')
    File_Control.delete_path('./temp/'+name+'-'+table+'/')
    File_Control.delete_path('./data/'+name+'-'+table+'/')

    return {'tables':tables}
  else:
    return {'tables':tables}


#file upload
@app.route('/upload', methods=['POST'])
def upload_files():
  table_id = request.form.get('id')
  name = request.form.get('name')
  files = request.files.getlist('files')
  if len(files) == 0:
    return {'result':'zero'}
  path='./temp/'+name+'-'+table_id+'/'
  uploaded_files=[]
  n=0
  for file in files:
    if file.filename == '':
      continue
    file_id=str(random.randint(1000000000,9999999999))
    filename = os.path.join(path, file_id+'-'+file.filename)
    file.save(filename)
    uploaded_files.append({'filename':file.filename, 'file_id': file_id, 'table_id': table_id, 'table':name,'isProcessed':False})
    n=n+1

  other_files=File_Control.open('./tables/files.pkl')
  other_files.extend(uploaded_files)
  File_Control.save('./tables/files.pkl',other_files)
  tables=File_Control.open('./tables/root.pkl')
  table=next(item for item in tables if item['id'] == table_id)
  tables=[item for item in tables if item['id'] != table_id]
  table['count']=n
  tables.append(table)
  File_Control.save('./tables/root.pkl',tables)

  return {'result':'success','files':other_files}

#Load all unprocessed documents currently created
@app.route('/files', methods=['GET'])
def unproc_files():
  #check if files object exist
  tables=File_Control.open('./tables/root.pkl')
  if File_Control.check_path('./tables/files.pkl'):
    files=File_Control.open('./tables/files.pkl')
  else:
    #create folder
    File_Control.create_path('./tables/')
    files=[]
    File_Control.save('./tables/files.pkl',files)
  files=files[-100:]
  return {'files':files,'tables':tables}

#delete an unprocessed file
@app.route('/delete_unproc_file', methods=['GET'])
def delete_file_unprocessed():
  file_id=request.args.get('file_id')
  filename=request.args.get('filename')
  table_id=request.args.get('table_id')
  table=request.args.get('table')
  files=File_Control.open('./tables/files.pkl')
  if File_Control.check_path('./data/'+table+'-'+table_id+'/'+file_id+'-'+filename+'.pkl'):
    file=File_Control.open('./data/'+table+'-'+table_id+'/'+file_id+'-'+filename+'.pkl')
    new_files=[item for item in files if item['file_id'] != file_id]
    vector=Euclid()
    deli=vector.delete(table,'file_id',file_id)
    if deli=='success':
      File_Control.save('./tables/files.pkl',new_files)
      File_Control.delete_file('./temp/'+table+'-'+table_id+'/'+file_id+'-'+filename)
      File_Control.delete_file('./data/'+table+'-'+table_id+'/'+file_id+'-'+filename+'.pkl')
      new_files=files[-100:]
      return {'files':new_files}
    else:
      files=files[-100:]
      return {'files':files}
  else:
    new_files=[item for item in files if item['file_id'] != file_id]
    File_Control.save('./tables/files.pkl',new_files)
    File_Control.delete_file('./temp/'+table+'-'+table_id+'/'+file_id+'-'+filename)
    new_files=files[-100:]
    return {'files':new_files}

#delete a file
@app.route('/delete_file', methods=['GET'])
def delete_file():
  file_id=request.args.get('file_id')
  filename=request.args.get('filename')
  table_id=request.args.get('table_id')
  table=request.args.get('table')
  files=File_Control.open('./tables/files.pkl')
  file=File_Control.open('./data/'+table+'-'+table_id+'/'+file_id+'-'+filename+'.pkl')
  new_files=[item for item in files if item['file_id'] != file_id]
  vector=Euclid()
  deli=vector.delete(table,'file_id',file_id)
  cite=file['citation']
  graph=Graph()
  dele_graph=graph.delete_node(cite)
  if deli=='success' and dele_graph=='success':
    File_Control.save('./tables/files.pkl',new_files)
    File_Control.delete_file('./temp/'+table+'-'+table_id+'/'+file_id+'-'+filename)
    File_Control.delete_file('./data/'+table+'-'+table_id+'/'+file_id+'-'+filename+'.pkl')
    return {'files':new_files}
  else:
    return {'files':files}

#process a file
@app.route('/proc_file', methods=['GET'])
def proc_file():
  file_id=request.args.get('file_id')
  filename=request.args.get('filename')
  table_id=request.args.get('table_id')
  table=request.args.get('table')
  file_path='./temp/'+table+'-'+table_id+'/'+file_id+'-'+filename
  collect=Collector()
  #process document using the AI
  proc=Process()
  tables=File_Control.open('./tables/root.pkl')
  tab=next(item for item in tables if item['id'] == table_id)
  if tab['type']=='ruling':
    if filename.lower().endswith('.pdf'):
      document=collect.pdf_raw(file_path)
    elif filename.lower().endswith('.docx'):
      document=collect.collect_docx(file_path)
    run=proc.court_proc(table, table_id, file_id, filename, document)
  elif tab['type']=='legislation':
    if filename.lower().endswith('.pdf'):
      document=collect.pdf_lines(file_path)
      run=proc.legislation_proc(table, table_id, file_id, filename, document)
    elif filename.lower().endswith('.docx'):
      document=collect.docx_styles(file_path)
      run=proc.legislation_docx(table, table_id, file_id, filename, document)
  else:
    #other methods of processing documents
    run={'result':'method for processing does not exist','content':{}}
  #updated status
  files=File_Control.open('./tables/files.pkl')
  if run['result']=='success':
    #add to table
    File_Control.save('./data/'+table+'-'+table_id+'/'+file_id+'-'+filename+'.pkl',run['content'])
    next(item for item in files if item['file_id'] == file_id)['isProcessed'] = True
    File_Control.save('./tables/files.pkl',files)

  else:
    print(run['result'])

  files=File_Control.open('./tables/files.pkl')
  files=files[-100:]
  return {'result':run['result'],'files':files}

#open a file
@app.route('/open_file', methods=['GET'])
def open_file():
  file_id=request.args.get('file_id')
  filename=request.args.get('filename')
  table_id=request.args.get('table_id')
  table=request.args.get('table')
  file=File_Control.open('./data/'+table+'-'+table_id+'/'+file_id+'-'+filename+'.pkl')
  tables=File_Control.open('./tables/root.pkl')
  tab=next(item for item in tables if item['id'] == table_id)
  cite=file['citation']
  graph=Graph()
  n=graph.search(cite)
  if tab['type']=='ruling':
    #collect the document
    file_path='./temp/'+table+'-'+table_id+'/'+file_id+'-'+filename
    collect=Collector()
    if filename.lower().endswith('.pdf'):
      document=collect.pdf_lines(file_path)
    elif filename.lower().endswith('.docx'):
      document=collect.docx_lines(file_path)
    file['raw']=document
  #print(n)

  return {'file':file,'type':tab['type'],'graph':n}

#load all processed files
@app.route('/load_processed', methods=['GET'])
def load_all_processed_files():
  #check if files object exist
  tables=File_Control.open('./tables/root.pkl')
  if File_Control.check_path('./tables/files.pkl'):
    files=File_Control.open('./tables/files.pkl')
  else:
    #create folder
    File_Control.create_path('./tables/')
    files=[]
    File_Control.save('./tables/files.pkl',files)

  processed_files=[]
  for file in files:
    if(file['isProcessed']==True):
      file_id=file['file_id']
      filename=file['filename']
      table_id=file['table_id']
      table=file['table']
      cont=File_Control.open('./data/'+table+'-'+table_id+'/'+file_id+'-'+filename+'.pkl')
      processed_files.append({'filename':filename, 'file_id': file_id, 'table_id': table_id, 'table':table, 'citation':cont['citation']})
  processed_files=processed_files[-20:]
  return {'files':processed_files,'tables':tables}

#section processing
@app.route('/section_proc', methods=['GET'])
def process_section():
  file_id=request.args.get('file_id')
  filename=request.args.get('filename')
  table_id=request.args.get('table_id')
  table=request.args.get('table')
  section_number=request.args.get('section_number')
  file=File_Control.open('./data/'+table+'-'+table_id+'/'+file_id+'-'+filename+'.pkl')
  section=next(item for item in file['sections'] if item['section_number'] == section_number)
  proc=Process()
  run=proc.section_process(section)

  return {'section':run}

#section processing
@app.route('/regenerate', methods=['GET'])
def document_regenerate():
  file_id=request.args.get('file_id')
  filename=request.args.get('filename')
  table_id=request.args.get('table_id')
  table=request.args.get('table')
  file_path='./temp/'+table+'-'+table_id+'/'+file_id+'-'+filename
  collect=Collector()
  #process document using the AI
  proc=Process()
  document=collect.pdf_raw(file_path)
  run=proc.court_proc(table, table_id, file_id, filename, document)
  files=File_Control.open('./tables/files.pkl')
  vector=Euclid()
  deli=vector.delete(table,'file_id',file_id)
  if deli=='success':
    if run['result']=='success':
      #add to table
      File_Control.save('./data/'+table+'-'+table_id+'/'+file_id+'-'+filename+'.pkl',run['content'])
      return {'result':run['result'],'file':run['content']}
    else:
      return {'result':'Error re-generating from the AI'}
  else:
    return {'result':'error deleting vector file'}

#upload changes to sections
@app.route('/upload_changes', methods=['POST'])
def upload_changes():
  data = request.get_json()
  file_id=data.get('file_id')
  filename=data.get('filename')
  table_id=data.get('table_id')
  table=data.get('table')
  document=data.get('document')
  vector=Euclid()
  deli=vector.delete(table,'file_id',file_id)
  if deli=='success':
    proc=Process()
    run=proc.update_legi(table, table_id, file_id, filename, document)
    if run=='success':
      File_Control.delete_file('./data/'+table+'-'+table_id+'/'+file_id+'-'+filename+'.pkl')
      File_Control.save('./data/'+table+'-'+table_id+'/'+file_id+'-'+filename+'.pkl',document)
      return {'result':'success'}
    else:
      return {'result':'Error embedding and adding to vector database'}
  else:
    return {'result':'Error deleting records from vector database'}

#do a raw search of the euclid database
@app.route('/raw_search', methods=['POST'])
def raw_search():
  data = request.get_json()
  table=data.get('table')
  query=data.get('query')
  vector=Euclid()
  r=vector.search(table,query,10)

  return {'documents':r}

#do a raw search of the euclid database
@app.route('/typing_search', methods=['POST'])
def typing_search():
  data = request.get_json()
  query=data.get('query')
  files=File_Control.open('./tables/files.pkl')
  processed_files=[]
  for file in files:
    if(file['isProcessed']==True):
      file_id=file['file_id']
      filename=file['filename']
      table_id=file['table_id']
      table=file['table']
      cont=File_Control.open('./data/'+table+'-'+table_id+'/'+file_id+'-'+filename+'.pkl')
      processed_files.append({'filename':filename, 'file_id': file_id, 'table_id': table_id, 'table':table, 'citation':cont['citation']})
  citations = [(file['citation'], file) for file in processed_files]
  matches = process.extract(query, [citation[0] for citation in citations], limit=20)
  matched_files=[]
  for file in matches:
    full=next(f for f in processed_files if f['citation']==file[0])
    matched_files.append(full)

  return jsonify({'documents':matched_files})

#deploy all documents into graph
@app.route('/deploy_graph', methods=['GET'])
def deploy_all_documents_to_graph():
  #check if files object exist
  tables=File_Control.open('./tables/root.pkl')
  files=File_Control.open('./tables/files.pkl')
  print('running deployment')
  documents=[]
  for file in files:
    type=next(item['type'] for item in tables if item['id'] == file['table_id'])
    file['type']=type
    documents.append(file)

  graph=Graph()
  n=graph.create_graph(documents)
  print('Done deploying')
  return {'result':'success'}

#deploy all documents into graph
@app.route('/show_graph', methods=['GET'])
def show_react_graph():
  graph=Graph()
  flow=graph.graph_data()
  return flow

if __name__=='__main__':
  app.run(host='0.0.0.0',port='8080')
