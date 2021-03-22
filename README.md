# Inware Translations

This repository is dedicated to the translation of the [Inware Android app](https://play.google.com/store/apps/details?id=com.evo.inware).

## Repository Structure

The repository is split into folders — one per language. These are named *values-X*, where *X* represents an ISO 639-1 language code. For example, *values-de* represents the German language. Each folder houses a *strings.xml* file.

## Contributing

The *strings.xml* files house the copy displayed in Inware. They comprise an entry for each bit of text. For example:

```xml
<string name="allow">Allow</string>
```

The `string` tags themselves must not be edited. To translate the above into Polish, you would use the folowing:

```xml
<string name="allow">Zezwól</string>
```

Some strings contain nested tags and/or placeholders:

```xml
<string name="cluster_number">Cluster #<xliff:g example="1" id="number_of_cluster">%d</xliff:g></string>
```

Placeholders (`%s` or `%d`) and `xliff:g` tags must not be edited. To translate the above into Polish, you would use the folowing:

```xml
<string name="cluster_number">Klaster #<xliff:g example="1" id="number_of_cluster">%d</xliff:g></string>
```

As such, a string of characters is translatable if preceded by `>` and suceeded by `<` or `<\`.

If a directory exists for your target language, edit the *strings.xml* file inside. Otherwise, create a directory following the naming convention described in “[Repository Structure](#repository-structure).” Inside, create a _strings.xml_ and use the following template:

```xml
<?xml version="1.0"?>
<resources xmlns:xliff="urn:oasis:names:tc:xliff:document:1.2">
    <!-- Add content here. -->
</resources>
```

Localised _strings.xml_ files should only contain translated copy. Find all source strings in [_values_/_strings.xml_](https://github.com/evowizz/inware-translations/blob/main/values/strings.xml), copy those you plan on translating into the localised _strings.xml_ file, and edit them. For example:

```xml
<?xml version="1.0"?>
<resources xmlns:xliff="urn:oasis:names:tc:xliff:document:1.2">
    <string name="os">System operacyjny</string>
    <string name="android_version">Wersja Androida</string>
    <string name="language">Język</string>
</resources>
```

Although this isn’t required, maintaing the order of the `string` tags from the source file will help other translators.

You are also welcome to correct existing translations. To do so, find the appropriate `string` tag in the localised _strings.xml_ file and edit its content. To submit a contribution for review, create a pull request. Thanks for your help!