<p align="center">
    <img width="200" src="logo/logo.png?raw=true" alt="Logsforhumans logo"/>
</p>

## What is logsforhumans

Logsforhumans logs all models changes for human beings (with descritive text of change).

## Usage
```python
from logsforhumans.models import generate_humanlogs

@generate_humanlogs
class Person(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
```

Just that! After that, all changes in your model can be get with:

```python
Person.objects.get().get_logs()
```

The return of `get_logs` function is a queryset of logsforhumans.HumanLog model:

```python
>>> john = Person.objects.create(name='John')
>>> john.get_logs()
<QuerySet [<HumanLog: The person "John" was created>]>
>>> john.name = 'John Wayne'
>>> john.save()
>>> john.get_logs()
<QuerySet [<HumanLog: The field Name was changed from "John" to "John Wayne"
>, <HumanLog: The person "John" was created>]>
```

The `HumanLog` model has the following fields:
- description (text field)
- creation_date (datetime field)
- updated_by (fk to User model that made the change)

## Instalation
1. Download the repository: `git clone https://github.com/rui-cadete-tecnologia/logsforhumans.git` inside your project
2. Put `logsforhumans` inside your `settings.INSTALLED_APPS`
3. Put `'logsforhumans.middleware.LogsForHumansMiddleware'` in the end of your
    `settings.MIDDLEWARE`


## What is not logsforhumans
Logsforhumans is not for model recovering! If you want to recover a version of your model, like an revision control, you can try https://github.com/treyhunner/django-simple-history

### Manually saving changes
Each model that is decorated with `generate_humanlogs` has a method called `add_log` where you can pass any text you want.


### Temporarily disabling logs
If you are going to make many changes in a model, with many saves you can skip the creation
of logs setting `skip_changelog=True` in your instance:
```python
john = Person.objects.get(name='John')
john.skip_changelog = True
john.name = 'John Merric'
john.save()  # this change is not saved
```

### Per-model field settings
If you have fields that you need log some change but dont want that information in log's description itself
(some examples are password fields, or file path of some importants file) you can use `LOGSFORHUMANS_IGNORE_DETAILS`
option, something like:

```python
from logsforhumans.models import generate_humanlogs

@generate_humanlogs
class User(models.Model):
    LOGSFORHUMANS_IGNORE_DETAILS = ('password', )

    password = PasswordModelField(...)
```

This will create a generic log without specify the exact value of field. You can customize the generic message that will be created with the settings `LOGSFORHUMANS_GENERIC_CHANGE_MESSAGE`

If you want completely ignore a field you can use `LOGSFORHUMANS_IGNORE_CHANGES` option:

```python
from logsforhumans.models import generate_humanlogs

@generate_humanlogs
class MyModel(models.Model):
    LOGSFORHUMANS_IGNORE_CHANGES = ('password', )
    password = PasswordModelField(...)
```

So, none log will be created when changing the password field.

### Customizing the change log to your language
For each operation (delete, normal field change, m2m field change, create field ...) logsforhumans has a settings field to customize the format.

The variables are:

- DEFAULT_DELETE_MESSAGE
- DEFAULT_CREATION_MESSAGE
- DEFAULT_FIELD_CHANGE_MESSAGE
- DEFAULT_M2M_FIELDS_MESSAGE
- DEFAULT_GENERIC_CHANGE

Each variable that can be overrided in your settings file. For example, the
actual default value for `DEFAULT_DELETE_MESSAGE` variable is:
```
The {model_name} "{instance_str}" (id={instance_id}) was deleted
```

If you dont want the ID of object in the log you can do:

```python
# settings.py
DEFAULT_DELETE_MESSAGE = 'The {model_name} "{instance_str}" was deleted'
```

When you delete your model the logs of it is not deleted.

Below are the string variable available for each model field operation:
- DEFAULT_DELETE_MESSAGE:
    - model_name: the name of model
    - instance_str: the string representation of model instance
    - instance_id: the instance id
- DEFAULT_CREATION_MESSAGE
    - model_name: the name of model
    - instance_str: the string representation of model instance
    - instance_id: the instance id
- DEFAULT_FIELD_CHANGE_MESSAGE
    - field_verbose_name: the verbose name of changed field
    - old_value: string representation of old field value
    - new_value: string representation of new field value
- DEFAULT_M2M_FIELDS_MESSAGE
    - item_model_name: the model's name of m2m item
    - item: the string representation of item
    - action: today can be: 'removido' and 'adicionado' (the portuguese version of 'removed' and 'added')
        this must be changed to a more flexible way. Feel free to pull request!
    - m2m_table: the intermediary m2m table
- DEFAULT_GENERIC_CHANGE
    - field_verbose_name: the verbose name of changed field
