#
# Copyright (C) 2010-2012 Red Hat, Inc.
# Authors:
# Thomas Woerner <twoerner@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import dbus
import dbus.service
import slip.dbus
import slip.dbus.service

from firewall.config import *
from firewall.dbus_utils import dbus_to_python
from firewall.config.dbus import *
from firewall.core.fw import Firewall
from firewall.core.io.zone import Zone
from firewall.core.logger import log
from firewall.server.decorators import *
from firewall.errors import *

############################################################################
#
# class FirewallDConfig
#
############################################################################

class FirewallDConfigZone(slip.dbus.service.Object):
    """FirewallD main class"""

    persistent = True
    """ Make FirewallD persistent. """
    default_polkit_auth_required = PK_ACTION_CONFIG
    """ Use PK_ACTION_INFO as a default """

    @handle_exceptions
    def __init__(self, config, zone, id, *args, **kwargs):
        super(FirewallDConfigZone, self).__init__(*args, **kwargs)
        self.config = config
        self.obj = zone
        self.id = id
        self.path = args[0]

    @dbus_handle_exceptions
    def __del__(self):
        pass

    @dbus_handle_exceptions
    def unregister(self):
        self.remove_from_connection()

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    # P R O P E R T I E S

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='ss',
                         out_signature='v')
    @dbus_handle_exceptions
    def Get(self, interface_name, property_name):
        # get a property
        log.debug1("Get('%s', '%s')", interface_name, property_name)

        if interface_name != DBUS_INTERFACE_CONFIG:
            raise dbus.exceptions.DBusException(
                "org.freedesktop.DBus.Error.UnknownInterface: "
                "FirewallD does not implement %s" % interface_name)

        if property_name == "name":
            return self.obj.name
        elif property_name == "filename":
            return self.obj.filename
        elif property_name == "path":
            return self.obj.path
        elif property_name == "defaults":
            return self.obj.defaults
        else:
            raise dbus.exceptions.DBusException(
                "org.freedesktop.DBus.Error.AccessDenied: "
                "Property '%s' isn't exported (or may not exist)" % \
                    property_name)

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='s',
                         out_signature='a{sv}')
    @dbus_handle_exceptions
    def GetAll(self, interface_name):
        log.debug1("GetAll('%s')", interface_name)

        if interface_name != DBUS_INTERFACE_CONFIG:
            raise dbus.exceptions.DBusException(
                "org.freedesktop.DBus.Error.UnknownInterface: "
                "FirewallD does not implement %s" % interface_name)

        return {
            'name': self.obj.name,
            'filename': self.obj.filename,
            'path': self.obj.path,
            'defaults': self.obj.defaults,
        }

    @slip.dbus.polkit.require_auth(PK_ACTION_CONFIG)
    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='ssv')
    @dbus_handle_exceptions
    def Set(self, interface_name, property_name, new_value):
        log.debug1("Set('%s', '%s', '%s')", interface_name, property_name,
                   new_value)

        if interface_name != DBUS_INTERFACE_CONFIG:
            raise dbus.exceptions.DBusException(
                "org.freedesktop.DBus.Error.UnknownInterface: "
                "FirewallD does not implement %s" % interface_name)

        raise dbus.exceptions.DBusException(
            "org.freedesktop.DBus.Error.AccessDenied: "
            "Property '%s' is not settable" % property_name)

    @dbus.service.signal(dbus.PROPERTIES_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface_name, changed_properties,
                          invalidated_properties):
        pass

    # S E T T I N G S

    @dbus_service_method(DBUS_INTERFACE_CONFIG, out_signature=Zone.DBUS_SIGNATURE)
    @dbus_handle_exceptions
    def getSettings(self, sender=None):
        """get settings for zone
        """
        log.debug1("config.zone.%d.getSettings()", self.id)
        return self.config.get_zone_config(self.obj)

    @dbus_service_method(DBUS_INTERFACE_CONFIG, in_signature=Zone.DBUS_SIGNATURE)
    @dbus_handle_exceptions
    def update(self, settings, sender=None):
        """update settings for zone
        """
        log.debug1("config.zone.%d.update('...')", self.id)
        self.obj = self.config.set_zone_config(self.obj,
                                               dbus_to_python(settings))
        self.Updated()

    @dbus_service_method(DBUS_INTERFACE_CONFIG)
    @dbus_handle_exceptions
    def loadDefaults(self, sender=None):
        """load default settings for builtin zone
        """
        log.debug1("config.zone.%d.loadDefaults()", self.id)
        self.obj = self.config.load_zone_defaults(self.obj)
        self.Updated()

    @dbus.service.signal(DBUS_INTERFACE_CONFIG)
    @dbus_handle_exceptions
    def Updated(self):
        log.debug1("config.zone.%d.Updated()", self.id)
        pass

    # R E M O V E

    @dbus_service_method(DBUS_INTERFACE_CONFIG)
    @dbus_handle_exceptions
    def remove(self, sender=None):
        """remove zone
        """
        log.debug1("config.zone.%d.removeZone()", self.id)
        self.config.remove_zone(self.obj)
        self.Removed()
        self.unregister()

    @dbus.service.signal(DBUS_INTERFACE_CONFIG)
    @dbus_handle_exceptions
    def Removed(self):
        log.debug1("config.zone.%d.Removed()", self.id)
        pass

    # R E N A M E

    @dbus_service_method(DBUS_INTERFACE_CONFIG, in_signature='s')
    @dbus_handle_exceptions
    def rename(self, name, sender=None):
        """rename zone
        """
        log.debug1("config.zone.%d.rename('%s')", self.id, name)
        self.config.rename_zone(self.obj, dbus_to_python(name))
        self.Renamed()

    @dbus.service.signal(DBUS_INTERFACE_CONFIG)
    @dbus_handle_exceptions
    def Renamed(self):
        log.debug1("config.zone.%d.Renamed()", self.id)
        pass