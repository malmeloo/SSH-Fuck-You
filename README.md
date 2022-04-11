# SSH-Fuck-You

Deliver an extensive "fuck you" to whoever is trying to get into your server.

This script simulates a regular SSH server to anyone scanning your network, and will happily ask them for a password.
However, after `n` (unsuccessful)
attempts, the server will let them in and start streaming any video file as ASCII art to their terminal, with no way out
except by killing their SSH client.

## Demo

_Low frame rate is due to recording. It's better in person, I promise ;)_

<details>
<summary>Show GIF</summary>
![demo](assets/demo.gif)
</details>

## Features

* Simulates regular OpenSSH server to make it appear less suspicious
* Very configurable, various options can be modified in `config.ini`
* Able to achieve near-original frame rates
* Always fills the full terminal window
* Automatically generates the necessary SSH keys for you
  (though you can also supply your own!)

## Installation

```shell
$ git clone https://github.com/DismissedGuy/ssh-fuck-you
$ cd ssh-fuck-you

$ python3 -m venv venv
$ . ./venv/bin/activate
$ pip3 install -r -U requirements.txt

$ python3 server.py
```

## Running on a non-privileged port

Since I do not recommend setting this up on a privileged port (since that would require running the script with root),
you can run it on some port `> 1023` and then add an following iptables rule like the following:

```shell
$ iptables -t nat -A OUTPUT -o lo -p tcp --dport 22 -j REDIRECT --to-port 5022
$ iptables -A PREROUTING -t nat -i eth0 -p tcp --dport 22 -j REDIRECT --to-port 5022
```

Make sure to swap the ports and interfaces out with your values. This will forward any connection attempts to port 22 to
the server running on port 5022, on both `eth0` and your loopback interface.

## Nmap scan output

The server spoofs SSH's version string to make it appear as a regular OpenSSH server. Here's the output of an nmap scan
on my local machine:

```shell
$ nmap -sC -sV 192.168.1.146 -p 22
Starting Nmap 7.80 ( https://nmap.org ) at 2022-04-11 21:25 CEST
Nmap scan report for pop-os-mike (192.168.1.146)
Host is up (0.00011s latency).

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 6.6.1p1 Ubuntu 2ubuntu2.13 (Ubuntu Linux; protocol 2.0)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 30.53 seconds
```

The version string is also configurable in `config.ini`.
