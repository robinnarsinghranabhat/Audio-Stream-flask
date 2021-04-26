var recording_button = document.getElementById('record');
var socket = io.connect('http://' + document.domain + ':' + location.port);

// Define the audio context guys
window.AudioContext = window.AudioContext || window.webkitAudioContext;

var audioContext = new AudioContext();
var audioInput = null,
    realAudioInput = null,
    inputPoint = null,
    recording = false;
var analyserContext = null;


socket.on('add-wavefile', function(url) {
    // add new recording to page
    audio = document.createElement('p');
    audio.innerHTML = '<audio src="' + url + '" controls>';
    document.getElementById('wavefiles').appendChild(audio);
});



function convertToMono( input ) {
    var splitter = audioContext.createChannelSplitter(2);
    var merger = audioContext.createChannelMerger(2);

    input.connect( splitter );
    splitter.connect( merger, 0, 0 );
    splitter.connect( merger, 0, 1 );
    return merger;
}

function gotStream(stream) {
    inputPoint = audioContext.createGain();

    // Create an AudioNode from the stream.
    realAudioInput = audioContext.createMediaStreamSource(stream);
    audioInput = realAudioInput;

    audioInput = convertToMono( audioInput );
    audioInput.connect(inputPoint);

    analyserNode = audioContext.createAnalyser();
    analyserNode.fftSize = 2048;
    inputPoint.connect( analyserNode );

    scriptNode = (audioContext.createScriptProcessor || audioContext.createJavaScriptNode).call(audioContext, 1024, 1, 1);
    scriptNode.onaudioprocess = function (audioEvent) {
        if (recording) {
            input = audioEvent.inputBuffer.getChannelData(0);

            // convert float audio data to 16-bit PCM
            var buffer = new ArrayBuffer(input.length * 2)
            var output = new DataView(buffer);

            for (var i = 0, offset = 0; i < input.length; i++, offset += 2) {
                var s = Math.max(-1, Math.min(1, input[i]));
                output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
            }
            socket.emit('write-audio', buffer);
        }
    }
    inputPoint.connect(scriptNode);
    scriptNode.connect(audioContext.destination);

    zeroGain = audioContext.createGain();
    zeroGain.gain.value = 0.0;
    inputPoint.connect( zeroGain );
    zeroGain.connect( audioContext.destination );
}

function initAudio() {
    if (!navigator.getUserMedia)
        navigator.getUserMedia = navigator.webkitGetUserMedia || navigator.mozGetUserMedia;
    if (!navigator.cancelAnimationFrame)
        navigator.cancelAnimationFrame = navigator.webkitCancelAnimationFrame || navigator.mozCancelAnimationFrame;
    if (!navigator.requestAnimationFrame)
        navigator.requestAnimationFrame = navigator.webkitRequestAnimationFrame || navigator.mozRequestAnimationFrame;

    navigator.getUserMedia({audio: true}, gotStream, function(e) {
        alert('Error getting audio');
        console.log(e);
    });
}


// Additional Function to glow image, and add recording css style
function toggleRecording( e ) {
    if (e.classList.contains('recording')) {
        // stop recording
        e.classList.remove('recording');
        recording = false;
        socket.emit('end-recording');
    } else {
        // start recording
        console.log(' emmiting at start-recording');
        e.classList.add('recording');
        recording = true;
        socket.emit('start-recording', {numChannels: 1, bps: 16, fps: parseInt(audioContext.sampleRate)});
    }
}

window.addEventListener('load', initAudio );

// One-liner to resume playback only when user interacted with the page, we don't want js to automatically record audio when mic access is given .. more secure !!
recording_button.addEventListener('click', function() {
    audioContext.resume().then(() => {
        console.log('Initializing Recording')
        toggleRecording(this);
    });
  });
