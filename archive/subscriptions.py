# -*- coding: utf-8 -*-
# @Author: Samuel Hill
# @Date:   2019-11-14 17:41:13
# @Last Modified by:   Samuel Hill
# @Last Modified time: 2019-11-17 17:54:35

import logging

LOGGER = logging.getLogger(__name__)


class Subscription(object):
    def __init__(self):
        self.subscribers = []
        self.new_data = None
        self.old_data = None

    def __repr__(self):
        rep = f'\nSubscription with subscribers: [{repr(self.subscribers)}]'
        rep += f'\n\tNew data: {self.new_data}\n\tOld data: {self.old_data}\n'
        return rep

    def __len__(self):
        return len(self.subscribers)

    def __getitem__(self, subscriber_number: int):
        return self.subscribers[subscriber_number]

    def subscribe(self, subscriber):
        self.subscribers.append(subscriber)

    def update(self, data):
        if self.old_data != data:
            self.new_data = data

    def retire_data(self):
        self.old_data = self.new_data
        self.new_data = None


class SubscriptionManager(dict):
    def add_new_subscription(self, pattern: str):
        self[pattern] = Subscription()

    def subscribe(self, pattern: str, subscriber):
        self[pattern].subscribe(subscriber)

    def update(self, pattern, *data):
        LOGGER.debug("Updating %s with %s", pattern, data)
        self[pattern].update(data)

    def retire_data(self, pattern):
        self[pattern].retire_data()


if __name__ == "__main__":
    subscriptions = SubscriptionManager()
    sub_text = '(test ?this)'

    subscriptions.add_new_subscription(sub_text)
    subscriptions.subscribe(sub_text, 'new guy')
    subscriptions.update(sub_text, [1, 2, 3])
    print(subscriptions)

    for pattern, subscription in subscriptions.items():
        if subscription.new_data is not None:
            for subscriber in subscription:
                print(subscriber)
        subscription.retire_data()

    print(subscriptions)
