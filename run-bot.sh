#! /bin/bash

BOT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $BOT_PATH && source venv/bin/activate && python main.py && deactivate && cd $OLDPATH || exit