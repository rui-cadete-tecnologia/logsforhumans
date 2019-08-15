# logsforhumans

Logsforhumans pretends logs all models changes to human beings (with descritive text).

Logsforhumans is not for model recovering!

### Logging a model
```python
from logsforhumans.models import LogForHumanModel

class MyAwesomeModel(LogForHumanModel):
    ...
```

And that's it! All changes to fields in that model will be logged.

### Retrieving the changes in a model
```python
from logsforhumans.models import HumanLog


@login_required
def logs_view(request, app, model, pk):
    humanlogs = HumanLog.objects.filter(
        model_name=model,
        app_label=app,
        object_id=pk)
    logs = list()
    title = u'Logs'
    for i in humanlogs:
        logs.append({
            'updated_by': i.updated_by,
            'creation_date': i.creation_date,
            'changes': [j for j in i.description.split('\n') if j]
        })
    return render_(request, 'logs.html', locals())
```

### Manually saving changes

Each model that inherits from `logsforhumans.models.LogForHumanModel` has a method called `add_log` where you can pass any text you want.


### Customizing the change log to your language
For each operation (delete, normal field change, m2m field change, create field ...) logsforhumans has a settings to custom the format.

Actually the variables are:

- DEFAULT_DELETE_MESSAGE
- DEFAULT_CREATION_MESSAGE
- DEFAULT_FIELD_CHANGE_MESSAGE
- DEFAULT_M2M_FIELDS_MESSAGE
- DEFAULT_GENERIC_CHANGE


### Per-model field settings
If you have fields that you need log some change but dont want that information in log itself
(some examples are password fields, or file path of some importants file) you can use `LOGSFORHUMANS_IGNORE_DETAILS`
option, something like:

```python
class MyModel(LogForHumanModel):
    LOGSFORHUMANS_IGNORE_DETAILS = ('password', )
    password = PasswordModelField(...)
```

This will create a generic log without specify the exact value of field. You can customize
the generic message that will be created with the settings `LOGSFORHUMANS_GENERIC_CHANGE_MESSAGE`

If you want completely ignore a field you can use `LOGSFORHUMANS_IGNORE_CHANGES` option:

```python
class MyModel(LogForHumanModel):
    LOGSFORHUMANS_IGNORE_DETAILS = ('password', )
    password = PasswordModelField(...)
```

So, none log will be created

