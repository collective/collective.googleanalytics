
def report_copied(ob, event):
    if event.object.title == event.original.title:
        ob.title = "Copy of %s" % event.original.title
