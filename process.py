import json
import traceback
from gpt import GPT
from euclid import Euclid
from langchain.text_splitter import TokenTextSplitter

class Process:
    def __init__(self):
        self.gpt = GPT()
        self.court = '''
        You are part of a legal citator system in Zimbabwe which is being used to analyze court rulings and format them in an appropriate way.
        The following is from a document of a legal ruling made by a court. You are required to analyze the ruling like you are a professional lawyer.
        Generate the following metadata in json format for this ruling following the rules provided for each data point:
        1. name: generate the correct case name for this case as provided in the ruling.
        2. citation: generate the Case Citation, this will be used to reference this case in the future and it key in this legal citation system.
           A citation should be of the format=> Case name + Court abbreviation + judgement number/judgement year.
           e.g. Bobson v Nyatwa & Anor HH 34/23 or State vs Gilbert SC 197/24
        3. court: this is the court in which the ruling is coming from e.g. High Court of Zimbabwe
        4. date: date when the ruling was made.
        5. case_number: the number of the case if provided.
        6. judges: an array of the name/s of judge/s that decided the matter e.g. ['Dube J','N. Moyo]
        7. summary: this is a summary of the matter which should be less than 300 words.
        8. keywords: pick up keywords that you see fit and put them in an array, the maximum number of keywords is 10.
        9. jurisdiction: The jurisdiction to which this case applies to (geographically or otherwise).
        10. parties: An array of all the parties involved in the case with the role of each applicant specified
            e.g. {'name':'Leeroy Ben','role':'applicant'} or {'name':'Troy Mary','role':'defendant'}
        11. case_law: An array of precedents that were used in this case, the description of the precedents themselves (the description should be more than 20 words highlighting the precedent in full but less than 200 words) and citations of their cases and a result of how that precedent was taken by the case i.e either referred or overruled.
            e.g. {'citation':'Mary v Gideon HH 87/12','desc':'Sets out the criteria for condonation applications.','result':'overruled'}
                 {'citation':'Bishi v Secretary for Education 1989 (2) ZLR 240 (H)','desc':'Discussion on balancing factors in condonation applications.', 'result':'referred'}
        12. legislation: An array of all the sections of legislations used or challenged in the ruling and the result as per interpretation of the ruling. The citation should just be of the legislation's name and the section number (no subsection or paragraphs needed). The description should be more than 20 words highlighting the context in which the legslation was used in full but less than 200 words.
            e.g. {'citation':'Mines Act 2019, Section 2','legislation':'Mines Act 2019','section':'Section 2', 'desc':'Legality of owning a mine','result':'referred'}
                 {'citation':'S.I 23 of 2020, Section 13','legislation':'S.I 23 of 2020','section':'Section 13','desc':'Regulations on operating a mine','result':'overruled'}
        13. set_precedent: An array of any new precedent (can be empty if there is no new precedent) which was established by this case and a description of those precedents in a summary of less than 200 words.
            e.g. {'precedent':'late noting of appeals','desc':'The late noting of an appeal should be done in reasonable time such that....'}
        '''

        # System prompt for splitting the entire document into sections
        self.section_scheduler_prompt = '''
        You are part of a legal document processing system in Zimbabwe used to process legal documents like legislations and contracts.
        You are provided with a legal document or part of it and you are required to locate where sections are and return a pointer for all those lines which will be used later to reconstruct the legal document in a structure manner.
        In the provided document, page number,number of line and line text are provided with the document being split into pages which are split into lines.
        Go through every page in their order and locate lines that initiate the start and end of a section and return a json format list pointing to the respective page and number of the line and include a title of the section.
        Your json should be of the format {'name':name of legislation or contract,'sections':[{'start':{'page':page number,'n':line number},'end':{'page':page number,'n':line number},'title':section title, 'section_number':section number}....other sections]}.
        Section number is a string which starts with the word 'Section' and then the section number e.g. Section 10 or Secton 10B. Name of legislation or contract is the provided name of that legislation in the document.
        '''

        #system prompt for processing sections
        self.section_processor='''
        You are part of a legal documents processor system in Zimbabwe which is used to process legal documents like legislations and contracts.
        You are provided with a section of one of the sections from a legal document and you are required to process the text of that section to remove watermark text, combine lines that belong to a single sub-section, paragraph, sub-paragraphs and finally create a summary of the section of up to 300 words but not more than the 300 wods.
        The text are provided as lines and you are required to combine the lines (and return the text in full as it is) as you see appropriate to make subsections, paragraphs and subparagraphs stand alone.
        If the provided section has no sub-section then combine all the lines together into two lines, 1 line for the title of the section and another for the section text.
        If the provided section has subsections,paragraphs and sub-paragraphs, then combine the section lines in a way that would seperate the subsections, paragraphs and sub-paragraphs.
        Take note that sub-section, paragraphs and sub-paragraphs might have introductory and wrap-up text, those should be put as their own lines also.
        You should return a json format object with the base structure: {'title':title of section as provided,'section_number':section number,'lines':[...processed lines],'summary':short summary of section}
        The following is an example of the json format highlighting elements of the structure:
        {'title':'Authority to submit reports and furnish information',
         'section_number':'Section 19',
         'lines':[
           'Authority to submit reports and furnish information',
           '(1)  In addition to the annual report which the Authority may be required, in terms of section 44 of the Audit and Exchequer Act [Chapter 22:03], to submit to the Minister the Authority—',
           '(a)  shall submit to the Minister such other reports as the Minister may require; and',
           '(b)  may submit to the Minister such other reports as the Board may deem advisable;',
           ' in regard to the operations, undertakings and property of the Authority.',
           '(2)  The Authority shall give to the Minister all such information relating to the undertakings of the Authority as the Minister may at any time require.',
           '(3) The Minister may lay before Parliament a report submitted to him by the Authority in terms of paragraph (a) or (b) of subsection (1).'
         ],
         'summary':...summary of the section,
        } 
        '''

    # Method for generating an analysis of court rulings
    def court_proc(self,table, table_id, file_id, filename, document):
        text = ''
        for t in document:
            text = text + t['text']
        messages = [{'role': 'system', 'content': [{'type': 'text', 'text': self.court}]}]
        messages.append({'role': 'user', 'content': [{'type': 'text', 'text': text}]})
        try:
            raw_json = self.gpt.json_gpt(messages)
            content = json.loads(raw_json)
            #embedd rulings
            vector=Euclid()
            meta={'citation':content['citation'],'table_id':table_id,'file_id':file_id,'filename':filename}
            cite=content['citation']+' : '+ content['summary']
            cite_embeds=self.gpt.embedd_text(cite)
            vector.add(table,cite,meta,cite_embeds)
            if len(content['case_law'])>0:
                case_l=''
                for c in content['case_law']:
                    case_l=case_l +'; '+ c['desc']
                #append
                case_embedds=self.gpt.embedd_text(case_l)
                vector.add(table,case_l,meta,case_embedds)
            if len(content['legislation'])>0:
                legi=''
                for c in content['legislation']:
                    legi=legi +'; '+ c['citation'] + ': '+c['desc']
                #append
                legi_embedds=self.gpt.embedd_text(legi)
                vector.add(table,legi,meta,legi_embedds)
            if len(content['set_precedent'])>0:
                case_l=''
                for c in content['set_precedent']:
                    case_l=case_l +'; '+ c['desc']
                #append
                case_embedds=self.gpt.embedd_text(case_l)
                vector.add(table,case_l,meta,case_embedds)
            return {'result': 'success', 'content': content}
        except Exception as e:
            print(traceback.format_exc())
            return {'result': str(e), 'content': {}}

    #splitt headings
    def combine_sections(self,sections_json,pages_json):
        combined_sections = {'sections': []}

        # Loop over each section from sections_json
        for section in sections_json:
            title = section['title']
            section_number=section['section_number']
            start_page = section['start']['page']
            start_line = section['start']['n']
            end_page = section['end']['page']
            end_line = section['end']['n']
            section_lines = []

            # Loop over the pages in pages_json
            for page in pages_json:
                page_number = page['page']

                # Process lines on the start page
                if page_number == start_page:
                    for line in page['lines']:
                        if start_page == end_page and start_line <= line['n'] <= end_line:
                            section_lines.append(line['text'])
                        elif page_number == start_page and end_line >= line['n'] >= start_line:
                            section_lines.append(line['text'])

                # Process lines on the end page
                elif page_number == end_page:
                    for line in page['lines']:
                        if line['n'] <= end_line:
                            section_lines.append(line['text'])

                # Process lines in between the start and end page
                elif start_page < page_number < end_page:
                    for line in page['lines']:
                        section_lines.append(line['text'])

            # Append the section with its lines to the combined_sections
            combined_sections['sections'].append({
                'section_number':section_number,
                'title': title,
                'lines': section_lines
            })

        return combined_sections

    # Method for generating an analysis of specific sections
    def section_process(self, section):
        messages = [{'role': 'system', 'content': [{'type': 'text', 'text': self.section_processor}]}]
        messages.append({'role': 'user', 'content': [{'type': 'text', 'text': str(section)}]})
        try:
            raw_json = self.gpt.json_gpt(messages)
            content = json.loads(raw_json)
            return {'result': 'success', 'content': content}
        except Exception as e:
            print(traceback.format_exc())
            return {'result': str(e), 'content': {}}

    # Method to create a schedule of sections
    def legislation_proc(self, table, table_id, file_id, filename, document):
        try:
            # Prepare the message with the system prompt and document text
            messages = [{'role': 'system', 'content': self.section_scheduler_prompt}]
            messages.append({'role': 'user', 'content': str(document)})
            
            # Send to GPT for scheduling sections
            raw_response = self.gpt.json_gpt(messages)
            sections = json.loads(raw_response)
            comb=self.combine_sections(sections['sections'],document)
            temp=[]
            for section in comb['sections']:
                updated_section=self.section_process(section)
                if updated_section['result']=='success':
                    temp.append(updated_section['content'])
                else:
                    temp.append(section)
            #combine for the document

            #embedd and submit sections
            meta={'citation':sections['name'],'table_id':table_id,'file_id':file_id,'filename':filename}
            vector=Euclid()
            for section in temp:
                sec_text=' '.join(section['lines'])
                fin=section['title']+' : '+ sec_text
                sec_embedd=self.gpt.embedd_text(fin)
                vector.add(table,fin,meta,sec_embedd)

            doc_final={'citation':sections['name'],'sections':temp}
            return {'result': 'success', 'content': doc_final}
        
        except Exception as e:
            print(traceback.format_exc())
            return {'result': str(e), 'content': {}}

    # Method to create a schedule of sections
    def legislation_docx(self, table, table_id, file_id, filename, document):
        try:
            new_document=[]
            size=len(document)
            i=0
            n=0
            while i<size:
                if i==0:
                    new_document.append(document[i])
                    n=n+1
                else:
                    #not first index
                    if document[i]['style']=='.provisionHeading' or document[i]['style']=='.crossHeading':
                        #check if the previous style is of a head
                        if document[i-1]['style']=='.provisionHeading' or document[i-1]['style']=='.crossHeading':
                            #last index is head too
                            new_document[n-1]['text']=document[i]['text']+ ' ' + new_document[n-1]['text']
                        else:
                            #last index is not head
                            new_document.append(document[i])
                            n=n+1
                    else:
                        #index is not a head at all
                        new_document.append(document[i])
                        n=n+1
                #end of first if
                i=i+1
            #combine section content
            sections = []
            citation = ''
            title = ''
            new_section = False
            section = []

            for para in new_document:
                if para['style'] == '.enactmentCitation':
                    citation = para['text']
                if para['style'] == '.enactmentTitle':
                    title = para['text']
                if para['style'] == '.provisionHeading' or para['style'] == '.crossHeading':
                    if new_section:
                        sections.append(section)
                        section=[]
                    new_section = True
                if para['style'] == '.scheduleNumber' or para['style'] == '.scheduleTitle':
                    if len(section)==1:
                        #there is an element for the schedule
                        section[0]=para
                    else:
                        #dont append if section is newe
                        if new_section:
                            sections.append(section)
                            section=[]
                    new_section = True
                if para['style'] == '.article':
                    if len(section)==1:
                        #there is an element for the article
                        section[0]=para
                    else:
                        if new_section:
                            sections.append(section)
                            section=[]
                    new_section = True
                if para['style']=='.partHeading':
                    if new_section:
                        sections.append(section)
                        section=[]
                    new_section=False
                if new_section:
                    section.append(para)
            #copy last remaining section
            if section!=[]:
                sections.append(section)
            #end for loop
            meta={'citation':title+', '+citation,'table_id':table_id,'file_id':file_id,'filename':filename}
            vector=Euclid()
            n=1
            new_sections=[]
            for section in sections:
                section_title=section[0]['text']
                temp=[]
                annots=[]
                for line in section:
                    if line['style']=='.annotationListItem' or line['style']=='.annotation':
                        annots.append(line['text'])
                    else:
                        t=line['text']
                        t=t.replace('\t',' ')
                        temp.append(t)
                new_sections.append({'title':section_title,'section_number':str(n),'lines':temp,'annotations':annots})
                n=n+1
            #end for
            for section in new_sections:
                sec_text=' '.join(section['lines'])
                splitter = TokenTextSplitter(chunk_size=500, chunk_overlap=150)
                chunks=splitter.split_text(sec_text)
                for chunk in chunks:
                    sec_embedd=self.gpt.embedd_text(chunk)
                    vector.add(table,sec_text,meta,sec_embedd)

            doc_final={'citation':title+', '+citation,'sections':new_sections}
            return {'result': 'success', 'content': doc_final}
        
        except Exception as e:
            print(traceback.format_exc())
            return {'result': str(e), 'content': {}}

    def update_legi(self, table, table_id, file_id, filename, document):
        #document was deleted
        try:
            #end for loop
            meta={'citation':document['citation'],'table_id':table_id,'file_id':file_id,'filename':filename}
            vector=Euclid()
            for section in document['sections']:
                sec_text=' '.join(section['lines'])
                splitter = TokenTextSplitter(chunk_size=500, chunk_overlap=150)
                chunks=splitter.split_text(sec_text)
                for chunk in chunks:
                    sec_embedd=self.gpt.embedd_text(chunk)
                    vector.add(table,sec_text,meta,sec_embedd)
            return 'success'
        
        except Exception as e:
            print(traceback.format_exc())
            return 'error'