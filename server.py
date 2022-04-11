#!/usr/bin/env python3

import configparser
import os.path
import sys
from abc import ABC

from twisted.conch import avatar
from twisted.conch.ssh import factory, keys, session
from twisted.conch.ssh.transport import SSHServerTransport
from twisted.cred import portal, error, credentials
from twisted.cred.checkers import ICredentialsChecker
from twisted.internet import reactor, protocol
from twisted.internet import task, defer
from twisted.python import components
from twisted.python import log
from zope.interface import implementer

import framegen

log.startLogging(sys.stderr)

conf = configparser.ConfigParser()
conf.read('config.ini')

keys_dir = conf['SERVER']['KeysDirectory']

SERVER_RSA_PRIVATE = os.path.join(keys_dir, 'id_rsa')
SERVER_RSA_PUBLIC = os.path.join(keys_dir, 'id_rsa.pub')
VIDEO_FILE_NAME = conf['SERVER']['VideoFile']
LOGIN_ATTEMPTS = int(conf['SERVER']['RequiredLoginAttempts'])

# fake server version string
new_ver = conf['SERVER']['VersionString'].encode()
print(f'Patching version string: {SSHServerTransport.ourVersionString} -> {new_ver}')
SSHServerTransport.ourVersionString = new_ver

os.makedirs(keys_dir, exist_ok=True)
if not os.path.isfile(SERVER_RSA_PRIVATE):
    print('Generating SSH keypair...')
    res = os.system(f'ssh-keygen -t rsa -b 4096 -f {SERVER_RSA_PRIVATE} -N "" >/dev/null')
    if res != 0:
        print('Error while generating keypair! Please make sure ssh-keygen is installed.')
        sys.exit(res)
    print('Pair generated')


class DummyAvatar(avatar.ConchUser):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.channelLookup.update({b"session": session.SSHSession})


# noinspection PyPep8Naming,PyMethodMayBeStatic
@implementer(portal.IRealm)
class DummyRealm:
    def requestAvatar(self, avatarId, _, *interfaces):
        return interfaces[0], DummyAvatar(avatarId), lambda: None


@implementer(ICredentialsChecker)
class LoginAttemptChecker:
    """
    A "credentials checker" that automatically allows anyone access
    after i attempts. Note that we cannot distinguish between clients
    here, so the attempt count is global but will be reset on each
    successful connection.

    Very secure, you should definitely use this in production!
    """
    credentialInterfaces = (
        credentials.IUsernamePassword,
        credentials.IUsernameHashedPassword,
    )

    def __init__(self, min_attempts):
        self.min_attempts = min_attempts
        self._attempt_count = 0

    def requestAvatarId(self, creds):
        self._attempt_count += 1
        print(creds)

        if self._attempt_count < self.min_attempts:
            return defer.fail(error.UnauthorizedLogin())

        return defer.succeed(True)


# noinspection PyArgumentList
class FuckYouProtocol(protocol.Protocol):
    """
    This is where the magic happens
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.frame_gen = framegen.AsciiFrameGenerator(VIDEO_FILE_NAME)
        self.frame_loop = task.LoopingCall(self.send_frame)

    def set_size(self, height, width):
        self.frame_gen.size = (width, height)

    def connectionMade(self):
        """Initialize project F.U."""
        self.frame_loop.start(1 / self.frame_gen.fps)

    def send_frame(self):
        self.transport.write('\x1b[2J')  # clear screen
        self.transport.write('\x1b[0;0H')  # set cursor pos to (0, 0)

        self.transport.write(next(self.frame_gen))

    def dataReceived(self, data):
        """Ignore data from client."""
        pass


# noinspection PyPep8Naming,PyMethodMayBeStatic
@implementer(session.ISession, session.ISessionSetEnv)
class DummySession:
    def __init__(self, _):
        self.proto = FuckYouProtocol()

    def openShell(self, transport):
        self.proto.makeConnection(transport)
        transport.makeConnection(session.wrapProtocol(self.proto))

    def setEnv(self, *_):
        pass

    def getPty(self, _, window_size, __):
        self.windowChanged(window_size)

    def closed(self):
        self.proto.frame_loop.stop()

    def windowChanged(self, size):
        self.proto.set_size(size[0], size[1])


class ServerFactory(factory.SSHFactory, ABC):
    protocol = SSHServerTransport

    publicKeys = {b"ssh-rsa": keys.Key.fromFile(SERVER_RSA_PUBLIC)}
    privateKeys = {b"ssh-rsa": keys.Key.fromFile(SERVER_RSA_PRIVATE)}

    def __init__(self, login_attempts):
        self.portal = portal.Portal(DummyRealm(), [
            LoginAttemptChecker(login_attempts)
        ])


components.registerAdapter(
    DummySession, DummyAvatar, session.ISession, session.ISessionSetEnv
)

if __name__ == "__main__":
    reactor.listenTCP(5022, ServerFactory(LOGIN_ATTEMPTS))
    reactor.run()
