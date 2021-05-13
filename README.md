# Building Simple Audio Streaming application with Flask and Socketio

Client side js records the audio and contionusly streams it into the server-side python/flask to save it

Further work : 
- In server side, after a specific size is met, automatically save it, pass it to deep learning model and emit back results in client side


flask-Socketio decorator skips a function if it's take more than a specified time .
that's why my model is not working. need to find a workaround 


LEARNED EVENTS : 

- Try to Emit from Message Queue Itself, But Redis was not working , let's use huey now for windows .. such a stupid problem
- 


IMP PRS: 

https://github.com/miguelgrinberg/Flask-SocketIO/issues/462 :: DISCUSSES HOW socket-io makes contact with redis
https://github.com/miguelgrinberg/Flask-SocketIO/issues/410 