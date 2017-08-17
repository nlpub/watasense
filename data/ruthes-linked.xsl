<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="text" encoding="utf-8"/>
  <xsl:strip-space elements="*"/>
  <xsl:key name="synonyms" match="/ruthes/synonyms/entry_rel" use="@concept_id"/>
  <xsl:key name="entries" match="/ruthes/entries/entry" use="@id"/>
  <xsl:key name="relations" match="/ruthes/relations/rel" use="@from"/>
  <xsl:template match="/">
    <xsl:for-each select="/ruthes/concepts/concept">
      <!-- id -->
      <xsl:value-of select="@id"/>
      <xsl:text>&#9;</xsl:text>
      <!-- count -->
      <xsl:value-of select="count(key('entries', key('synonyms', @id)/@entry_id))"/>
      <xsl:text>&#9;</xsl:text>
      <!-- synonyms -->
      <xsl:for-each select="key('entries', key('synonyms', @id)/@entry_id)">
        <xsl:if test="position() &gt; 1">
          <xsl:text>|</xsl:text>
        </xsl:if>
        <xsl:value-of select="name"/>
      </xsl:for-each>
      <xsl:text>&#9;</xsl:text>
      <!-- count -->
      <xsl:value-of select="count(key('entries', key('synonyms', key('relations', @id)[@name = &quot;ВЫШЕ&quot; or @name = &quot;ЦЕЛОЕ&quot;]/@to)/@entry_id))"/>
      <xsl:text>&#9;</xsl:text>
      <!-- relations -->
      <xsl:for-each select="key('entries', key('synonyms', key('relations', @id)[@name = &quot;ВЫШЕ&quot; or @name = &quot;ЦЕЛОЕ&quot;]/@to)/@entry_id)">
        <xsl:if test="position() &gt; 1">
          <xsl:text>|</xsl:text>
        </xsl:if>
        <xsl:value-of select="name"/>
      </xsl:for-each>
      <xsl:text>&#10;</xsl:text>
    </xsl:for-each>
  </xsl:template>
</xsl:stylesheet>
