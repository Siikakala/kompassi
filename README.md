# Kompassi Event Management System

[![Build Status](https://travis-ci.org/tracon/kompassi.svg?branch=master)](https://travis-ci.org/tracon/kompassi)
[![Sponsored by Leonidas](https://img.shields.io/badge/sponsored%20by-leonidas-389fc1.svg)](https://leonidasoy.fi/opensource)

Formerly known as Turska and ConDB. Simple web app for managing (Tra)con stuff. Work in progress.

## Getting Started

### The Easy Way

Provided you have Docker (tested: 17.03 CE) and Docker Compose (tested: 0.11.2), you should get up and running by simply executing

    docker-compose up

Now open http://localhost:8000 in your browser. A superuser `mahti` with password `mahti` has been created for you.

When the dependencies change, you need to add `--build` to `docker-compose up` to rebuild the Docker image.

Run tests:

    docker-compose -f docker-compose.test.yml up --exit-code-from test

Or if you're running a pre-1.2.0 Docker Compose:

    docker-compose -f docker-compose.test.yml up --abort-on-container-exit

### The Hard Way

**NOTE:** Python 3.6 or greater is required. Python 2.7 is not supported.

    python3.6 -m venv venv3-kompassi
    source venv3-kompassi/bin/activate
    git clone https://github.com/tracon/kompassi.git
    cd kompassi
    pip install -U pip setuptools wheel
    pip install -r requirements.txt
    ./manage.py setup
    ./manage.py runserver
    iexplore http://localhost:8000

`./manage.py setup --test` created a test user account `mahti` with password `mahti`.

## Docker

A Docker image is available as [tracon/kompassi](https://hub.docker.com/r/tracon/kompassi/). More info to follow.

## License

    The MIT License (MIT)

    Copyright © 2009-2017 Santtu Pajukanta
    Copyright © 2009–2015 Jussi Sorjonen
    Copyright © 2011 Petri Haikonen
    Copyright © 2012-2015 Meeri Panula
    Copyright © 2013 Esa Ollitervo
    Copyright © 2014 Pekka Wallendahl
    Copyright © 2014-2016 Jyrki Launonen
    Copyright © 2015 Miika Ojamo
    Copyright © 2015-2016 Aarni Koskela, Santeri Hiltunen

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

For third-party component licenses, see [LICENSE](https://github.com/tracon/kompassi/blob/master/LICENSE.md).

The work of Santtu Pajukanta on Kompassi has been partially sponsored by [Leonidas Oy](https://leonidasoy.fi/opensource).
