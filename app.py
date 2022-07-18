import os
from aws_cdk import (
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
)
import aws_cdk as cdk
from constructs import Construct
import lambda_handler

class SaveSpotifyMixes(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        bucket = s3.Bucket(self, 'MySpotifyHistory', versioned=True)

        # Firstly read the lambda function definition from the handler.py file
        with open('lambda_handler.py', encoding='utf8') as func:
            handlerCode = func.read()

        # Define the lambda based on the code read from the handler.py file
        readFunc = lambda_.Function(
            self, 'ReadSpotifyDailyMix',
            code=lambda_.InlineCode(handlerCode),
            handler='lambda_handler.handler',
            timeout=cdk.Duration.seconds(600),
            runtime=lambda_.Runtime.PYTHON_3_9
        )

        # Now define the rule by which to execute the lambda function
        rule = events.Rule(self, 'RefreshDaily', schedule=events.Schedule.rate(cdk.Duration.days(1)))

        # And assign the function to the rule
        rule.add_target(targets.LambdaFunction(readFunc))

        

# Establish the application
app = cdk.App()
# Instantiate the stack using a default user credential
SaveSpotifyMixes(app, "SaveSpotifyMixesStack", env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')))
# Synthesise the established application and associated stack
app.synth()
