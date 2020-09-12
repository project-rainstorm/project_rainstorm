import React, { useEffect, useState } from "react";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import Divider from "@material-ui/core/Divider";
import ListItemText from "@material-ui/core/ListItemText";
import ListItemAvatar from "@material-ui/core/ListItemAvatar";
import Avatar from "@material-ui/core/Avatar";
import Typography from "@material-ui/core/Typography";
import style from "./style.module.css";

export default function ActivePage() {
  const [services, setServices] = useState(null);

  useEffect(() => {
    fetch("/services")
      .then(res => res.json())
      .then(data => {
        setServices(data.data);
      });
  }, []);

  return (
    <div>
      <List className={style.root}>
        {services &&
          services.map(service => {
            const settings = JSON.parse(service.settings);

            return (
              <ListItem alignItems="flex-start">
                <ListItemAvatar>
                  <Avatar
                    alt="Remy Sharp"
                    src={
                      "http://nuve.local:5000/static/images/" +
                      service.name +
                      ".jpg"
                    }
                  />
                </ListItemAvatar>
                <ListItemText
                  primary={settings.name}
                  secondary={
                    <React.Fragment>
                      <Typography
                        component="span"
                        variant="body2"
                        className={style.inline}
                        color="textPrimary"
                      ></Typography>
                      {settings.description}
                    </React.Fragment>
                  }
                />
              </ListItem>
            );
          })}
      </List>
    </div>
  );
}
