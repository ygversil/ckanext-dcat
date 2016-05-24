import json

from rdflib import URIRef
from rdflib.namespace import Namespace, SKOS

from pylons import config

from ckanext.dcat.profiles import RDFProfile


DCAT = Namespace("http://www.w3.org/ns/dcat#")


class LabeledConceptsDCATAPProfile(RDFProfile):
    """An RDF profile based on the *actual* DCAT-AP specification.

    In this specification, dataset themes and publisher types are SKOS
    concepts. For each of these concepts, this profile will put insert
    its label instead of its URI.

    It depends on the European DCAT-AP profile (``euro_dcat_ap``).
    """

    def _replace_concept_uris_by_labels(self, dataset_dict, key):
        """Replace in ``dataset_dict[extras]``, for the given key, all
        values which are URIs with their corresponding labels."""
        concept_dict = next((d for d in dataset_dict.get('extras', [])
                             if d['key'] == key), {})
        try:
            is_list = True
            concept_uris = json.loads(concept_dict.get('value', '[]'))
        except ValueError:  # Not a list
            is_list = False
            concept_uris = [concept_dict.get('value', u'')]
        for concept_uri in concept_uris[:]:  # Copy list to edit original
            labels = self.g.preferredLabel(
                URIRef(concept_uri),
                lang=config.get('ckan.locale_default', 'en')
            )
            if labels:
                _, label = labels[0]
                label = unicode(label)
                concept_uris.remove(concept_uri)
                concept_uris.append(label)
        if not is_list:
            concept_uris = concept_uris.pop()
        concept_dict['value'] = json.dumps(concept_uris, ensure_ascii=False)

    def parse_dataset(self, dataset_dict, dataset_ref):
        self._replace_concept_uris_by_labels(dataset_dict, 'theme')
        self._replace_concept_uris_by_labels(dataset_dict, 'publisher_type')
        return dataset_dict


class EurovocGroupsDCATAPProfile(RDFProfile):
    """An RDF profile based on the DCAT-AP specification and that will try to
    put datasets into Eurovoc groups.

    Thus, it requires that those groups already exist in CKAN and that they
    are identified (``id`` property) by URI (begins with
    ``http://eurovoc.europa.eu``).

    This profile also depends on the European DCAT-AP profile
    (``euro_dcat_ap``).
    """

    def parse_dataset(self, dataset_dict, dataset_ref):
        #  Groups (Eurovoc domains)
        dataset_dict['groups'] = []
        theme_uris = self._object_value_list(dataset_ref, DCAT.theme)
        for theme_uri in theme_uris:
            scheme_uri = self._object_value(URIRef(theme_uri), SKOS.inScheme)
            dataset_dict['groups'].append({'id': scheme_uri})
        return dataset_dict
