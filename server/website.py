from flask import render_template, send_file, redirect
from time import time
from time import sleep
from os import urandom
import json
import random
from g4f import ChatCompletion
from flask import Flask, request, Response
from flask_cors import CORS
from g4f.Provider import (
    Aichat,
    Bing,
    H2o,
    DeepAi,
    GetGpt,
)

class Website:
    def __init__(self, app) -> None:
        self.app = app
        self.routes = {
            '/': {
                'function': lambda: redirect('/chat'),
                'methods': ['GET', 'POST']
            },
            '/chat/': {
                'function': self._index,
                'methods': ['GET', 'POST']
            },
            '/chat/<conversation_id>': {
                'function': self._chat,
                'methods': ['GET', 'POST']
            },
            '/assets/<folder>/<file>': {
                'function': self._assets,
                'methods': ['GET', 'POST']
            },
            '/v1/chat/completions': {
                'function': self._chat_completions,
                'methods': ['POST']
            },
            
        }

    def _chat(self, conversation_id):
        if not '-' in conversation_id:
            return redirect(f'/chat')

        return render_template('index.html', chat_id=conversation_id)

    def _index(self):
        return render_template('index.html', chat_id=f'{urandom(4).hex()}-{urandom(2).hex()}-{urandom(2).hex()}-{urandom(2).hex()}-{hex(int(time() * 1000))[2:]}')

    def _assets(self, folder: str, file: str):
        try:
            return send_file(f"./../client/{folder}/{file}", as_attachment=False)
        except:
            return "File not found", 404
    def _chat_completions(self):
        streaming = request.json.get('stream', False)
        model = request.json.get('model', 'gpt-3.5-turbo')
        messages = request.json.get('messages')
        
        response = ChatCompletion.create(model=model, stream=streaming,
                                        messages=messages,provider=GetGpt)
        
        if not streaming:
            while 'curl_cffi.requests.errors.RequestsError' in response:
                response = ChatCompletion.create(model=model, stream=streaming,
                                                messages=messages,provider=GetGpt)

            completion_timestamp = int(time())
            completion_id = ''.join(random.choices(
                'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=28))
            print({
                'id': 'chatcmpl-%s' % completion_id,
                'object': 'chat.completion',
                'created': completion_timestamp,
                'model': model,
                'usage': {
                    'prompt_tokens': None,
                    'completion_tokens': None,
                    'total_tokens': None
                },
                'choices': [{
                    'message': {
                        'role': 'assistant',
                        'content': response
                    },
                    'finish_reason': 'stop',
                    'index': 0
                }]
            })
            return {
                'id': 'chatcmpl-%s' % completion_id,
                'object': 'chat.completion',
                'created': completion_timestamp,
                'model': model,
                'usage': {
                    'prompt_tokens': None,
                    'completion_tokens': None,
                    'total_tokens': None
                },
                'choices': [{
                    'message': {
                        'role': 'assistant',
                        'content': response
                    },
                    'finish_reason': 'stop',
                    'index': 0
                }]
            }

        def stream():
            for token in response:
                completion_timestamp = int(time())
                completion_id = ''.join(random.choices(
                    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=28))

                completion_data = {
                    'id': f'chatcmpl-{completion_id}',
                    'object': 'chat.completion.chunk',
                    'created': completion_timestamp,
                    'model': 'gpt-3.5-turbo-0301',
                    'choices': [
                        {
                            'delta': {
                                'content': token
                            },
                            'index': 0,
                            'finish_reason': None
                        }
                    ]
                }

                yield 'data: %s\n\n' % json.dumps(completion_data, separators=(',' ':'))
                sleep(0.05)

        return self.app.response_class(stream(), mimetype='text/event-stream')