class Lobby(object):
    def __init__(self):
        self.users = []

    def join(self, user):
        self.users.append(user)

    def leave(self, user):
        try:
            self.users.remove(user)
        except:
            pass

    def broadcastServerMessage(self, msg):
        for u in self.users:
            u.sendCommand("SERVER_MSG", {
                "type": "voiced",
                "msg": msg
            })

    def broadcastUserMessage(self, user, msg):
        for u in self.users:
            u.sendCommand("USER_MSG", {
                "user": user.username,
                "type": "voiced",
                "msg": msg
            })

    def whisperedServerMessage(self, user, recipient, msg):
        for u in self.users:
            if u is recipient:
                u.sendCommand("USER_MSG", {
                    "user": user.username,
                    "type": "whispered",
                    "msg": msg
                })

    def whisperedUserMessage(self, user, recipient, msg):
        for u in self.users:
            if u is recipient:
                u.sendCommand("USER_MSG", {
                    "user": user.username,
                    "type": "whispered",
                    "msg": msg
                })