import eventlet
eventlet.monkey_patch()

import soundfile as sf

import time
import numpy as np
from threading import Thread

from flask import Flask, render_template, session, url_for, current_app
from flask_socketio import SocketIO, emit
from background_audio_processor import predict_audio_from_stream


from engineio.payload import Payload
Payload.max_decode_packets = 50

import uuid
import wave
import sys
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
app.config['FILEDIR'] = 'static/_files/'
app.config['COUNT'] = 0
app.config['file_count'] = 0

socketio = SocketIO(app)

thread = None
global_latest_stream = None

def initiate_recording(options):

    try:
        session['wavefile'].close()
    except:
        pass
    
    """Start recording audio from the client."""

    session['options'] = options

    # id = uuid.uuid4().hex  # server-side filename
    # session['wavename'] = 'robin_audio.wav'
    session['wavename'] = str(app.config['file_count']) + '.wav'
    wf = wave.open(app.config['FILEDIR'] + session['wavename'], 'wb')
    wf.setnchannels(options.get('numChannels', 1))
    wf.setsampwidth(options.get('bps', 16) // 8)
    wf.setframerate(options.get('fps', 44100))
    print('Sample rate is : ',  options )

    session['wavefile'] = wf
    session['collected_frames'] = []

    app.config['file_count'] += 1



@socketio.on('start-recording')
def start_recording(options):
    """Start recording audio from the client."""

    print('Initializing  the Recorder')
    initiate_recording(options)



@socketio.on('end-recording')
def end_recording():
    """Stop recording audio from the client."""
    emit('add-wavefile', url_for('static',
                                 filename='_files/' + session['wavename']))
    session['wavefile'].close()
    del session['wavefile']
    del session['wavename']

@socketio.on('write-audio')
def write_audio(data):
    print('COUNT IS AT : ', app.config['COUNT'])
    """Write a chunk of audio from the client."""
    if app.config['COUNT'] < 172:
        session['collected_frames'].append(data)
        app.config['COUNT'] += 1
    else:
        # final_data_size = ((( 44100 * 8 ) - (2048 * 172 )) // 2 ) + 136 + 68
        final_data_size = 272*2
        session['collected_frames'].append(data[:final_data_size])
        session['wavefile'].writeframes(b"".join(session['collected_frames']))

        
        global global_latest_stream
        global_latest_stream = np.frombuffer(b"".join(session['collected_frames']), dtype=np.int16)
        global_latest_stream = (global_latest_stream - global_latest_stream.mean())/ global_latest_stream.std()
        ## Save this audio chunk in browser as well , Although Completely useless and optional
        # emit('add-wavefile', url_for('static',
        #                          filename='_files/' + session['wavename']))

        session['collected_frames'] = []
        app.config['COUNT'] = 0
        
        initiate_recording(session['options'])

        # if app.config['file_count'] > 0:
        #     print('INSIDE PREDICTION')
        #     try:
        #         temp_name = str(app.config['file_count']-1) + '.wav'
        #         file_path = f"./static/_files/{temp_name}"  
        #         job = q.enqueue(predict_audio, file_path)                

        #         # output = app.config['model'].predict()
        #         # print('OUTPUT IS : ', output)
        #         # emit('model-output', output)
        #     except Exception as e:
        #         print('REDIS BROKE ', e)
        #         emit('model-output', 'Predictions not incoming !! ')
                # print('Error in Prediction -> ', e)

def background_thread_from_stream(app):

    with app.app_context():
        while True:
            print('BACKGROUND THREAD!!!')
                
            
            start = time.time()
            if global_latest_stream is not None:
                output = predict_audio_from_stream(global_latest_stream) 
            else:
                output = 'Predictions awaiting'
            elapsed = time.time() - start

            ## we make sure our thread uses exactly 4 seconds, during this time, another thread will record new incoming audio
            if (4-elapsed) > 0:
                time.sleep(4-elapsed)

            socketio.emit('model-output', output)
            print('EMMISION SUCCESSFUL :', output)


def background_thread(app):

    with app.app_context():
    # with app.test_request_context('/'):

        while True:
            print('BACKGROUND THREAD!!!')
            if app.config['file_count'] > 0:
                # try:
                    
                    temp_name = str(app.config['file_count']-1) + '.wav'
                    file_path = f"./static/_files/{temp_name}" 
                    
                    start = time.time()
                    output = predict_audio(file_path) 
                    elapsed = time.time() - start

                    if (4-elapsed) > 0:
                        time.sleep(4-elapsed)

                    socketio.emit('model-output', output)
                    print('EMMISION SUCCESSFUL :', output)


                # except Exception as e:
                #     time.sleep(3)
                #     print('ERROR  ', e)
                #     socketio.emit('model-output', 'Predictions not incoming !! ')
            
            else:
                time.sleep(2)
                print('WAITING ... current count is ', app.config['file_count'])
                socketio.emit('model-output', 'AWAITING EMMISSION !! ')


@app.route('/')
def sessions():
    return render_template('session.html')
    
@socketio.on('connect')
def on_connect():
    global thread
    if thread is None:
        thread = socketio.start_background_task(target=background_thread_from_stream, app=current_app._get_current_object())


if __name__ == '__main__':
    socketio.run(app, debug=True)
