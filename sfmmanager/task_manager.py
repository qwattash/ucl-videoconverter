from celery import chain

import tasks
from sfmmanager.models import Video


class TaskManager(object):
    
    """
    video_id id of video to reconstruct
    """
    def __init__(self, video_id):
        self.target = video_id

    """
    Process video
    processing is done usinga celery task chain
    priority and numberof runing tasks can be configured
    in the celery module
    """
    def run(self):
        video = Video.objects.get(pk=self.target)
        video.status = Video.STATUS_PENDING
        video.save()
        res = chain(tasks.deleteProcessingData.s(self.target),
                    tasks.extractFrames.s(), 
                    tasks.processFrames.s(), 
                    tasks.processOutput.s())()
