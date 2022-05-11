<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "contributions" %>

<h2>
	${_('Contribution')} ${ctx.name}
</h2>
<div id="segments" class="tab-pane active">
	${request.get_datatable('values', h.models.Value, contribution=ctx).render()}
</div>

<%def name="sidebar()">
	<%util:well>
		<h3>${h.link(request, ctx.language)}</h3>
		${util.language_meta(lang=ctx.language)}
	</%util:well>
</%def>
