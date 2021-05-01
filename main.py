from flask import Flask, render_template, session, url_for
from flask_socketio import SocketIO, emit
# from audio_model import 

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


@app.before_first_request
def load_model():
    from audio_model import PredictAudio
    app.config['model'] = PredictAudio(sampling_rate=48000)



@app.route('/')
def sessions():
    return render_template('session.html')

def initiate_recording(options):

    try:
        session['wavefile'].close()
    except:
        pass
    
    """Start recording audio from the client."""

    session['options'] = options

    id = uuid.uuid4().hex  # server-side filename
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
        

        ## Save this audio chunk in browser as well 
        emit('add-wavefile', url_for('static',
                                 filename='_files/' + session['wavename']))

        
        session['collected_frames'] = []
        app.config['COUNT'] = 0
        
        initiate_recording(session['options'])

        if app.config['file_count'] > 0:
            print('INSIDE PREDICTION')
            try:
                temp_name = str(app.config['file_count']-1) + '.wav'
                file_path = f"./static/_files/{temp_name}"  
                app.config['model'].filepath = file_path

                output = app.config['model'].predict()
                print('OUTPUT IS : ', output)
                emit('model-output', output)
            except Exception as e:
                emit('model-output', 'Predictions not incoming !! ')
                # print('Error in Prediction -> ', e)


@socketio.on_error  # handles all namespaces without an explicit error handler
def default_error_handler(e):
    print('ERROR AT ', e)


if __name__ == '__main__':
    socketio.run(app, debug=True)
