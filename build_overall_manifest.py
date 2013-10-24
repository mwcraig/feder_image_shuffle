import os
from astropy.table import Table, Column
from astropy.io import registry as io_registry
import logging

logger = logging.getLogger(__name__)


class InfoTree(Table):
    """
    Class to construct a concatenated table from a hierarchy of directories
    containing tables (ideally identical in structure).

    The table constructed by this class is always a masked table.
    """
    def __init__(self, top_directory=None, **kwd):
        """
        Parameters
        ----------

        top_directory : string, optional
            Path to top of directory tree. May be set after initialization.

        All other keywords are passed on to the initializer of ``astropy.table``
        """
        self._data_source_colname = 'File location'
        _user_masked_keyword = kwd.pop('masked', None)
        if _user_masked_keyword is not None:
            logger.warning(('Cannot set the masked property for these tables. '
                           'It is always True.'))

        super(InfoTree, self).__init__(masked=True, **kwd)

        self._table_file_name = 'Manifest.txt'

        if top_directory is not None:
            self.top = top_directory

    @property
    def top(self):
        """
        Name of directory at the top of the directory tree
        """
        return self._top

    @top.setter
    def top(self, directory):
        """
        Parameters
        ----------

        directory : string
            Path to directory at the top of the directory tree.
        """
        self._top = directory
        self._build_table()

    @property
    def table_file_name(self):
        return self._table_file_name

    def _build_table(self):
        from collections import OrderedDict
        # define dictionary used to store table values while reading
        # in each individual table
        self._pending_colnames = OrderedDict()
        #self._cutoff = 0
        for path, dirs, files in os.walk(self.top, topdown=False):
            if files:
                logger.debug('Working on directory %s', path)
                self._add_table_if_present(path, files)
            #if self._cutoff > 15:
            #    break

        for colname in self._pending_colnames:
            column = Column(name=colname,
                            data=self._pending_colnames[colname])
            self.add_column(column)
        self._pending_colnames = OrderedDict()

    def _add_table_if_present(self, path, files):
        """
        Add the contents of a table from disk to this table.

        Parameters
        ----------

        path : string
            Name of directory containing files.
        files : list
            List of one or more files in the directory path.
        """
        if self.table_file_name not in files:
            logger.debug('No tables found in directory %s', path)
            return
        #self._cutoff += 1
        current_table_path = os.path.join(path, self.table_file_name)
        this_table = Table.read(current_table_path, format='ascii')
        self._add_to_table(this_table, path)
        self._current_table_path = None

    def _add_to_table(self, table, data_path):
        """
        Add a table from disk to this table.

        Parameters
        ----------

        table : an astropy.table Table instance
            Table to be appended

        data_path : str
            Name of directory in which this table resides
        """
        if not self._pending_colnames:
            for column in table.colnames:
                self._pending_colnames[column] = []
            self._pending_colnames[self._data_source_colname] = []

        input_columns = table.colnames
        input_columns.append(self._data_source_colname)
        if input_columns != self._pending_colnames.keys():
            raise(ValueError,
                  'Column names do not match in {}'.format(data_path))
        for column in table.colnames:
            self._pending_colnames[column].extend(list(table[column]))
        data_path_list = [data_path] * len(table)
        self._pending_colnames[self._data_source_colname].extend(data_path_list)
