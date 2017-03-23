from slackclient import SlackClient
import re

"""
Load the opensubtitles dialog corpus.
"""
    

class SlackReactionData:

    def __init__(self, dirName):

        self.reaction_re = re.compile('(^:[a-z_]+:)')

        slack_token = ''

        self.sc = SlackClient(slack_token)

        #Clear outfile
        self.outfile = 'slack.txt'
        with open(self.outfile, "w"):
            pass

        #Find general channel
        #self.general_channel = next(obj for obj in channels_call['channels'] if obj['is_general'] == True)

        channels_call = self.sc.api_call(
            "channels.list",
            exclude_archived=True
        )

        groups_call = self.sc.api_call(
            "groups.list",
            exclude_archived=True
        )
        
        self.last_message = None
        self.conversations = []
        
        for group in groups_call['groups']:
            print('Capturing group {}', group['name'])
            self.last_message = None
            self.conversations = self.getMessagesFromGroup(self.conversations, group)

        for channel in channels_call['channels']:
            print('Capturing channel {}', channel['name'])
            self.last_message = None
            self.conversations = self.getMessagesFromChannel(self.conversations, channel)


    def getLine(self, sentence):
        line = {}
        line["text"] = sentence.strip().lower() #self.tag_re.sub('', sentence).replace('\\\'','\'').strip().lower()
        return line

    def getMainReaction(self, message):
        main_reaction = '[no_reaction]'

        main_reaction_count = 0
        
        if 'reactions' in message:
            for r in message['reactions']:
                if r['count'] == main_reaction_count:
                    #Add another reaction to the main reaction
                    main_reaction = main_reaction + ' :' +  r['name'] + ':'
                elif r['count'] > main_reaction_count:
                    main_reaction_count = r['count']
                    main_reaction = ':' + r['name'] + ':'
        return main_reaction

    def getMessagesFromChannel(self, conversations, channel, latest=None):

        if 'id' not in channel:
            print('skiping channel {}', channel)
            return conversations

        if latest is None:
            messages = self.sc.api_call(
                "channels.history",
                channel=channel['id'],
                count=1000

            )
        else:    
            messages = self.sc.api_call(
                "channels.history",
                channel=channel['id'],
                latest=latest,
                count=1000
            )
       
        if 'messages' not in messages:
            print('skiping channel {}', channel['name'])
            return conversations

        message_count = 0
        new_latest = ""
        for m in messages['messages']:
            new_latest = m['ts']
            if m['type'] == 'message':
                tmp = {}
                tmp['lines'] = []
                tmp['lines'].append(self.getLine(m['text']))
                tmp['lines'].append(self.getLine(self.getMainReaction(m)))
                message_count += 1
                conversations.append(tmp)

                with open(self.outfile, 'a') as out:
                    out.write(str(tmp) + '\n')

                #Check for message reaction
                if self.last_message is not None:
                    clean_message = m['text'].strip().lower()
                    match = self.reaction_re.match(clean_message)

                    if match is not None:
                        tmp = {}
                        tmp['lines'] = []
                        tmp['lines'].append(self.getLine(self.last_message['text']))
                        tmp['lines'].append(self.getLine(match.group()))
                        message_count += 1
                        conversations.append(tmp)

                        with open(self.outfile, 'a') as out:
                            out.write(str(tmp) + '\n')
                
                self.last_message = m
        print("\n")
        print("{} messages captured now.".format(message_count))
        print("{} messages in total.".format(len(conversations)))       

        if messages['has_more']:
            conversations = self.getMessagesFromChannel(conversations, channel, new_latest)

        return conversations

    def getMessagesFromGroup(self, conversations, group, latest=None):

        if 'id' not in group or group['is_mpim'] == True:
            print('skiping channel {}', group)
            return conversations

        if latest is None:
            messages = self.sc.api_call(
                "groups.history",
                channel=group['id'],
                count=1000

            )
        else:    
            messages = self.sc.api_call(
                "groups.history",
                channel=group['id'],
                latest=latest,
                count=1000
            )
       
        if 'messages' not in messages:
            print(messages)
            print('skiping group {}', group['name'])
            return conversations

        message_count = 0
        new_latest = ""
        for m in messages['messages']:
            new_latest = m['ts']
            if m['type'] == 'message' and 'text' in m:
                tmp = {}
                tmp['lines'] = []
                tmp['lines'].append(self.getLine(m['text']))
                tmp['lines'].append(self.getLine(self.getMainReaction(m)))
                message_count += 1
                conversations.append(tmp)

                with open(self.outfile, 'a') as out:
                    out.write(str(tmp) + '\n')

                #Check for message reaction
                if self.last_message is not None:
                    clean_message = m['text'].strip().lower()
                    match = self.reaction_re.match(clean_message)

                    if match is not None:
                        tmp = {}
                        tmp['lines'] = []
                        tmp['lines'].append(self.getLine(self.last_message['text']))
                        tmp['lines'].append(self.getLine(match.group()))
                        message_count += 1
                        conversations.append(tmp)

                        with open(self.outfile, 'a') as out:
                            out.write(str(tmp) + '\n')
                
                self.last_message = m

        print("\n")
        print("{} messages captured now.".format(message_count))
        print("{} messages in total.".format(len(conversations)))       

        if messages['has_more']:
            conversations = self.getMessagesFromGroup(conversations, group, new_latest)

        return conversations

    def getConversations(self):
        return self.conversations