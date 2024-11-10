import tweepy
from pydantic import BaseModel, Field

GET_TWEETS_PROMPT = """
This tool will get tweets from a Twitter user. The tool takes the username of the Twitter user as input."""


class GetTweetsInput(BaseModel):
    """Input argument schema for get tweets action."""

    username: str = Field(
        ...,
        description="The username of the Twitter user to get tweets from.",
    )


def get_tweets(client: tweepy.Client, username: str) -> str:
    """Get tweets from a Twitter user.

    Args:
        client (tweepy.Client): The tweepy client to use.
        username (str): The username of the Twitter user to get tweets from.

    Returns:
        str: A message containing the tweets from the user.

    """
    try:
        user_id = get_user_id(username)
        if isinstance(user_id, str):
            return user_id
        latest_tweets = client.get_users_tweets(
            id=user_id, max_results=5, exclude=['retweets', 'replies'])
    except tweepy.TweepyException as e:
        return f"Error getting tweets: {str(e)}"

    for t in latest_tweets.data:
        print(t.text)

    return latest_tweets.data


def get_user_id(client: tweepy.Client, username: str):
    try:
        user = client.get_user(username=username)
        return user.data.id
    except tweepy.TweepyException as e:
        return f"Error getting User ID: {str(e)}"