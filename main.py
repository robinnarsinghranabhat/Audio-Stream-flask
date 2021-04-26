from flask import Flask, render_template, session, url_for
from flask_socketio import SocketIO, emit

import uuid
import wave

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
app.config['FILEDIR'] = 'static/_files/'

socketio = SocketIO(app)


@app.route('/')
def sessions():
    return render_template('session.html')

@socketio.on('start-recording')
def start_recording(options):
    """Start recording audio from the client."""
    id = uuid.uuid4().hex  # server-side filename
    session['wavename'] = 'robin_record' + '.wav'
    wf = wave.open(app.config['FILEDIR'] + session['wavename'], 'wb')
    wf.setnchannels(options.get('numChannels', 1))
    wf.setsampwidth(options.get('bps', 16) // 8)
    wf.setframerate(options.get('fps', 44100))
    session['wavefile'] = wf

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
    """Write a chunk of audio from the client."""
    session['wavefile'].writeframes(data)


if __name__ == '__main__':
    socketio.run(app, debug=True)
