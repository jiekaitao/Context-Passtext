# Context-Passtext

To speed up the process of learning asyncronously through video lectures, here is a simple python program that automatically passes in the context of your video lecture to LLMs like ChatGPT so that questions can be spoken as if you're raising a hand in a classroom.
It does this by listening to your computer microphone, picking up the last 5 minutes or so of any video lectures and your spoken word.
Optimized for MacOS... you may have to change some libraries (mainly keystroke monitoring) if you use any other operating system.

# Usage:

Run this program, and when you have some confusion on what your video lecture, pause the video and say your question. Finally, press CTRL + q and wait about 3 seconds for the voice to say "copied a question."
This takes a screenshot of your primary monitor, passes in the last five minutes of your lecturer's words, and your question to your system's clipboard.

Finally, paste into ChatGPT or any LLM that supports vision.
