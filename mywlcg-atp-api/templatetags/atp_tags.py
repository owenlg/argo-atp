from django import template
from django.core.exceptions import ObjectDoesNotExist
#from mywlcg.mdb.models import SiteGroup
from atp.orm.models import SiteGroup

register = template.Library()


@register.simple_tag
def roc_name(sites):
    try:
        sg = SiteGroup.objects.get(
            site__sitename__iexact = sites.all()[0].sitename,
            groups__group_type__typename__icontains = 'Region',
            isdeleted__iexact = 'N'
        )
        return sg.groups.groupname
    except ObjectDoesNotExist:
        return ''
