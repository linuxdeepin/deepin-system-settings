#ifdef HAVE_CONFIG_H
# include "config.h"
#endif

#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#include <glib.h>
#include <glib-object.h>

#include <dbus/dbus-glib.h>
#include <dbus/dbus-glib-lowlevel.h>

#include "deepin-datetime.h"

static DBUSGProxy * get_bus_proxy(DBusGConnection *connection)
{
    DBusGProxy *bus_proxy;
    bus_proxy = dbus_g_proxy_new_for_name(connection,
                                          DBUS_SERVICE_DBUS,
                                          DBUS_PATH_DBUS,
                                          DBUS_INTERFACE_DBUS);
    
    return bus_proxy;
}

#define BUS_NAME "com.linuxdeepin.datetime"

static gboolean acquire_name_on_proxy(DBusGProxy *bus_proxy)
{
    GError *error;
    guint result;
    gboolean res;
    gboolean ret;
    
    ret = FALSE;
    if(bus_proxy == NULL){
        goto out;
    }
    
    error = NULL;

    res = dbus_g_proxy_call(bus_proxy, 
                            "RequestName",
                            &error,
                            G_TYPE_STRING, BUS_NAME,
                            G_TYPE_UINT, 0,
                            G_TYPE_INVALID,
                            G_TYPE_UINT, &result,
                            G_TYPE_INVALID);

    if(!res){
        if(error != NULL){
            g_warning("Failed to acquire %s:%s", BUS_NAME, error->message);
            g_error_free(error);
        }else {
            g_warining("Failed to acquire %s", BUS_NAME);
        }
        goto out;
    }

    if(result != DBUS_REQUEST_NAME_REPLY_PRIMARY_OWNER){
        if(error != NULL){
            g_warning("Failed to acquire %s:%s", BUS_NAME, error->message);
            g_error_free(error);
        }else{
            g_waring("Failed to acquire %s", BUS_NAME);
        }
        goto out;
    }

    ret = TRUE;
out:
    return ret;

}

static DBusGConnection * get_system_bus(void)
{
    GError *error;
    DBusGConnection *bus;
    error = NULL;
    bus = dbus_g_bus_get(DBUS_BUS_SYSTEM, &error);
    if(bus == NULL){
        g_warning("Couldn't connect to system bus:%s", error->message);
        g_error_free(error);
    }
    return bus;
}

int main(int argc, char **argv)
{
    GMainLoop *loop;
    DeepinDatetime *datetime;
    DBusGProxy *bus_proxy;
    DBusGConnection *connection;
    int ret;
    
    ret = 1;
    if(!g_thread_supported()){
        g_thread_init(NULL);
    }
    dbus_g_thread_init();
    g_type_init();

    connection = get_system_bus();
    if(connection == NULL){
        g_warning("connection == NULL; bailing out");
        goto out;
    }

    bus_proxy = get_bus_proxy(connection);
    if(bus_proxy == NULL){
        g_warning("Couldn't construct bus_proxy object");
        goto out;
    }

    if(!acquire_name_on_proxy(bus_proxy)){
        g_warning("Couldn't acquire name");
        goto out;
    }

    datetime = deepin_datetime_new();
    if(datetime == NULL){
        g_warning("datetime == NULL");
        goto out;
    }
    
    loop = g_main_loop_new(NULL, FALSE);
    g_main_loop_run(loop);

    g_object_unref(datetime);
    g_main_loop_unref(loop);

    ret = 0;

out:
    printf("go to out\n");
    return ret;
}
